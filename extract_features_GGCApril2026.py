from collections import defaultdict
import pandas as pd

from readers import LatinReader
from readers import AncientGreekReader
from features import LatinFeatures
from features import AncientGreekFeatures

import spacy

from tqdm import tqdm

#new
import os

# NORM = False

# List features to check here
raw_features = [
    "word_count",
    "sentence_count",
    "sentence_length",
    "fraction_sentence_relative",
    "relative_clause_length",
    "_relative_clause_sent_count",
]

#LATIN BLOCK
#normed_features = "alius antequam atque_consonant conjunction cum_clause demonstrative dum gerundive idem interrogative ipse iste o_interjection personal preposition priusquam quidam quin quominus reflexive si superlative ut".split()


#GREEK BLOCK:
normed_features = [
    "interrogatives",
    "conditional_markers",
    "personal_pronouns",
    "demonstrative",
    "allos",
    "autos",
    "reflexive",
    "sentences_with_vocative_omega",
    "superlative",
    "conjunction",
    "circumstantial_markers",
    "hina",
    "hopos",
    "ws",
    "temporal_causal_markers",
    "wste_not_preceded_by_eta",
    "particles",
    "men",
]
#///DO I NEED .SPLIT()????


if __name__ == "__main__":
    #readers = [LatinReader] #//do i need to modify this?
    readers = [AncientGreekReader]
    #feature_sets = [LatinFeatures] #//modify this to change feature sets?
    feature_sets = [AncientGreekFeatures]
    #root_base = "data/curated_epic/"
    #root_base = "data/curated_hist/"
    #root_base = "data/working_texts_complete/"
    #root_base = "data/working_texts_complete_chunked1/"
    #root_base = "data/curated_epic_chunked_dec27/"
    #this is the directory to pull from:
    #root_base = 'Users/gavingcook/Documents/PostdocLatinWork/stylometry/data/curated_epic_chunked_dec27/'
    #//NOTE - DID I FORGET TO OPEN THAT PATH WITH A '/'^^^^?
    #full paths are screwing with something down stream - the 'READER = reader(ROOT)' line

    #FILES I HAVE RUN:
    #root_base = "data/curated_epic_chunked_dec27/"
    #root_base = "data/curated_hist/"
    #root_base = "data/working_texts_complete/" #<- gets stuck on a 2.6 mb txt file jesus
    #root_base = "data/working_texts_complete_minusEpistolae/"
    root_base = "data/working-texts/"
    #will this work?
    #nlp = spacy.load('la_core_web_lg')
    #nlp.max_length = 5000000
    # #new on Sept 1, 2025
    # #nlp.max_length -> set
    # #one document has ~2,600,000 chars
    #


    def get_text_length(root, fileid):
        filepath = os.path.join(root, fileid)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            return len(text)
        except Exception as e:
            print(f"Could not read {fileid}: {e}")
            return None

    def find_second_camelcase_position(s: str) -> int:
        for i, c in enumerate(s):
            if c.isupper() and i > 0:
                return i
        return -1

    def get_reader_language(reader):
        return reader.__name__[
            : find_second_camelcase_position(reader.__name__)
        ].lower()

    normed_features_data = defaultdict(list)
    unnormed_features_data = defaultdict(list)

    for reader, feature_set in tqdm(zip(readers, feature_sets)):
        root = f"{root_base}{get_reader_language(reader)}"
        READER = reader(root)

        #--new lines:
        print("Corpus folder:", os.path.abspath(root))
        print("Files found:", len(READER.fileids()))
        print("First filenames:", READER.fileids()[:10])


        #print("Reader nlp.max_length =", READER.nlp.max_length)
        #additoin on sept 1, 2025
        #READER = reader(root, nlp = nlp)



        MAX_LEN = 2_500_000 #spacy default


        #testing block:
        #for fileid in tqdm(READER.fileids()[:2]):
        for fileid in tqdm(READER.fileids()):
            text_len = get_text_length(root, fileid)

            if text_len is None:
                print(f"Skipping {fileid}: unreadable")
                continue

            if text_len > MAX_LEN:
                print(f"SKIPPING {fileid}: length {text_len} > {MAX_LEN}")
                continue

            print(f"Processing {fileid} (len={text_len})")

            try:
                #RAW_FEATURES = feature_set(READER, fileid, norm=False, annotations=False)
                RAW_FEATURES = feature_set(READER, fileid, norm=False, annotations=False, verbose=False)
                print("DEBUG:")
                print("CSV word_count:", RAW_FEATURES.word_count)
                print("First word-list items:", repr(RAW_FEATURES.words[:30]))
                print("First tagged items:", repr(RAW_FEATURES.flat_tagged_sents[:5]))
                print("Document code points:", len(RAW_FEATURES.doc))
                print("Document UTF-8 bytes:", len(RAW_FEATURES.doc.encode("utf-8")))
                print("Whitespace chunks:", len(RAW_FEATURES.doc.split()))
            except Exception as e:
                print(f"ERROR in {fileid}: {e}")
                continue

            for feature in raw_features:
                normed_features_data[fileid].append(
                    {feature: getattr(RAW_FEATURES, feature)}
                )
                unnormed_features_data[fileid].append(
                    {feature: getattr(RAW_FEATURES, feature)}
                )

            #NORMED_FEATURES = feature_set(READER, fileid, norm=True, annotations=False)
            NORMED_FEATURES = feature_set(READER, fileid, norm=True, annotations=False, verbose=False)
            for feature in normed_features:
                normed_features_data[fileid].append(
                    {feature: getattr(NORMED_FEATURES, feature)}
                )

            UNNORMED_FEATURES = feature_set(
                #READER, fileid, norm=False, annotations=False
                READER, fileid, norm=False, annotations=False, verbose=False
            )
            for feature in normed_features:
                unnormed_features_data[fileid].append(
                    {feature: getattr(UNNORMED_FEATURES, feature)}
                )

    index, normed_data = zip(*normed_features_data.items())
    normed_data = [
        {k: v for d in i for k, v in d.items()} for i in normed_data
    ]  # cf. https://stackoverflow.com/a/69492942

    index, unnormed_data = zip(*unnormed_features_data.items())
    unnormed_data = [
        {k: v for d in i for k, v in d.items()} for i in unnormed_data
    ]  # cf. https://stackoverflow.com/a/69492942

    # Python, create timestamp for filename
    import datetime

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")


    #normed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-normed"
    #normed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-normed-curated_hist"
    #normed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-normed-working_texts_complete_minusEpistolae"
    #normed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-normed-working_texts_complete"
    normed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-Greek"
    print('normed outfile path = ' + normed_outfile)
    #unnormed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-raw"
    #unnormed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-raw-curated_hist"
    #unnormed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-raw-working_texts_complete_minusEpistolae"
    #unnormed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-raw-working_texts_complete"
    unnormed_outfile = f"/Users/gavingcook/Documents/PostdocLatinWork/Stylometry/GGCoutput/output/features/{timestamp}-Greek"
    normed_pickle_outfile = normed_outfile + ".pickle"
    normed_csv_outfile = normed_outfile + ".csv"
    unnormed_pickle_outfile = unnormed_outfile + ".pickle"
    unnormed_csv_outfile = unnormed_outfile + ".csv"

    df = pd.DataFrame(normed_data, index=index)
    df.to_pickle(normed_pickle_outfile)
    df.to_csv(normed_csv_outfile)

    df = pd.DataFrame(unnormed_data, index=index)
    df.to_pickle(unnormed_pickle_outfile)
    df.to_csv(unnormed_csv_outfile)
