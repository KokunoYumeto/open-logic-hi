# Open Logic Project — हिन्दी कार्यशील अनुवाद

**अभी पढ़ें:**
[`00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.pdf`](reader/00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.pdf)

- स्थायी हिन्दी DOI: <https://doi.org/10.5281/zenodo.21920511>
- यह सटीक संस्करण: <https://doi.org/10.5281/zenodo.21940471>
- पूर्ण स्रोत और audit package:
  [HI-OLP-PUB-0003 release](https://github.com/KokunoYumeto/open-logic-hi/releases/tag/HI-OLP-PUB-0003)
- भाषा: हिन्दी, देवनागरी (`hi-Deva-IN`)

यह Open Logic Project की **158 स्वीकृत source TeX files** का
machine-assisted हिन्दी working edition है। इन files में 59,955 मापे गए
English source words हैं। सामने रखा reader 211 pages का searchable PDF है:
चार परिचय/pages और 207 translated-content pages। हर स्वीकृत tranche PDF में
सफलतापूर्वक बना, और cumulative reader ने 300-dpi all-page raster, search/copy,
internal-link, font-embedding, Devanagari-shaping और visual checks पास किए।

यह अभी पूरे 722-file Open Logic corpus का अनुवाद नहीं है। शेष 564 files पर
काम जारी है। Human review, peer review, critical edition या PDF/UA
certification का दावा नहीं किया जाता। अगला acceptance tranche प्रथम-क्रम
अर्थविज्ञान की आठ files है; वे इस checkpoint में जानबूझकर शामिल नहीं हैं।

Source authority: [OpenLogicProject/OpenLogic at commit
`9620cc73f9c8e0ad003c514a5d3748f29611c4c0`](https://github.com/OpenLogicProject/OpenLogic/tree/9620cc73f9c8e0ad003c514a5d3748f29611c4c0),
tree `f67757bb9305b173634082ab4cefd5601a707a34`, CC BY 4.0. Translation and
Hindi build-support changes are indicated. No endorsement is asserted.

## Repository map

- `reader/`: current cumulative reader, front and centre
- `source/locale/hi/content/`: exactly 158 accepted Hindi source files
- `source/wrappers/` and `source/tools/`: accepted standalone wrappers and
  deterministic reader/QA tooling
- `evidence/ACCEPTED_FILES.csv`: exact source/target hashes for the boundary
- `evidence/`: concise coverage, source, QA, and DOI state
- release file 01: editable source package with matching frozen English files
- release file 02: full provenance, terminology, decisions, failures, logs,
  renders, and QA receipts

Stable identifiers apply to the maintained Hindi work lineage. Scheduling
chapters do not receive separate DOI lineages.
