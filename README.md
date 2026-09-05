# ओपन लॉजिक परियोजना — संपूर्ण हिंदी संस्करण

*Open Logic Project — Complete Hindi Edition*

अन्य भाषाओं के संस्करण और साझा अनुवाद मानक [Open Logic translations hub](https://github.com/KokunoYumeto/OpenLogic-translations) में सूचीबद्ध हैं।

मुख्य पुस्तक `00_OpenLogic_hi-Deva-IN_reader.pdf` है: 975 A4 पृष्ठ, हिंदी और देवनागरी।
यह जमी हुई स्रोत प्रति की सभी 722 सामग्री-TeX फ़ाइलों को सम्मिलित करती है।
इस संख्या में अध्याय-चालक भी हैं; यह शब्द-गणना नहीं है। पुराने 842-पृष्ठीय
संकलन से छूटे 80 स्रोत-पथ अब सम्मिलित हैं। समान खंडों वाले चार वैकल्पिक
अध्याय-चालकों की संपादकीय टिप्पणियाँ रखी गई हैं; साझा खंड दोहराए नहीं गए।

स्रोत: `OpenLogicProject/OpenLogic`, कमिट
`9620cc73f9c8e0ad003c514a5d3748f29611c4c0`। मूल लेखक: Open Logic Project।
हिंदी रूपांतरण और अक्षर-संयोजन: AI typesetting & translation। कृत्रिम-बुद्धि
मॉडल: OpenAI 5.6 Sol, Ultra mode। स्रोत की CC BY 4.0 अनुज्ञप्ति और अलग
चिह्नित परिसंपत्तियों की शर्तें यथावत हैं। मूल परियोजना का अनुमोदन नहीं माना गया है।

## इस संग्रह में क्या है

- `hindi-translation/`: वर्तमान हिंदी पाठ, औपचारिक संकेत, चित्र-सहायक और फ़ॉन्ट।
- `source-frozen/`: जमी हुई मूल अंग्रेज़ी स्रोत प्रति।
- `qa/reconciliation/`: स्रोत-सम्मिलन मानचित्र, जाँच-प्रमाण, सुधार और उनके मूल पाठ।
- `lane-control/`, `terminology/`, `publication-history/`: निर्णय और पूर्व कार्य का अभिलेख।
- `historical/2026-08-18/`: पुराने संकलन की ऐतिहासिक सामग्री; वर्तमान पुस्तक नहीं।
- `build/reconciled/`: वर्तमान संकलन के अभिलेख।
- `PUBLIC_REDACTIONS.json`: निजी नाम हटाने की सीमित सूची; स्थानीय मूल सुरक्षित हैं।

## पुनः संकलन

Windows पर MiKTeX/XeLaTeX और latexmk स्थापित होने पर PowerShell में चलाएँ:
`powershell -File rebuild/rebuild.ps1 -Mode full`। यह पूरे संकलन के लिए
`Global\InterlanguageTeXSlotV1` नामक मशीन-व्यापी mutex लेता है और उसे अंत में
छोड़ता है। स्रोत-संकेत और पाठ स्थिर हैं; PDF समय-मुद्रा के कारण पुनर्निर्मित PDF
का पूरा बाइट-हैश अलग हो सकता है।

## जाँच और सीमाएँ

स्रोत-पथ सम्मिलन, SHA-256, संकलन, संदर्भ, फ़ॉन्ट और हिंदी पाठ-निष्कर्षण जाँचे गए हैं।
दृश्य और अर्थगत समीक्षा का वास्तविक विस्तार `qa/reconciliation/ACCEPTANCE.json`
में है। प्रत्येक पृष्ठ की स्वतंत्र समीक्षा, मानव/सहकर्मी समीक्षा, आलोचनात्मक
संस्करण या PDF/UA प्रमाणीकरण का दावा नहीं है। स्रोत के प्रयोगात्मक अथवा अपूर्ण
खंडों की चेतावनियाँ सुरक्षित हैं; पूरा अनुवाद उन मूल प्रमाणों को पूर्ण घोषित नहीं करता।

स्थायी DOI: https://doi.org/10.5281/zenodo.21920511
GitHub: https://github.com/KokunoYumeto/open-logic-hi


## Terminology and difficult decisions

`terminology/SUBSTANTIVE_DECISION_LOG.jsonl` contains 400 traceable records:
357 terminology choices, 40 translation/typesetting corrections, and 3 shared
configuration decisions. It records exact literal source/target locations,
authority statements, rationales, alternatives, uncertainty, and precise
questions for asynchronous expert correction. Retrospective reconstructions
are labelled retrospective. The 20 provisional terms are summarized in
`terminology/PROVISIONAL_REVIEW_QUEUE.md`. Missing expertise is not a gap or
publication hold; the current wording remains a documented, correctable choice.
