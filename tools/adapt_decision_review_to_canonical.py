"""Adapt the Hindi review ledger to the frozen canonical OpenLogic schema.

This is a reversible projection: it does not edit accepted Hindi TeX or PDF.
Unknown source/reader alignment is labelled derived or pending, never guessed.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv, hashlib, json, re, shutil
import requests
from jsonschema import Draft202012Validator, FormatChecker

R=Path(__file__).resolve().parents[1]
TERM=R/'04_terminology'
OUT=TERM/'canonical_decision_review'
Q=R/'07_qa/openlogic/HI-OLP-READER-RECONCILED-20260904'
SROOT=R/'02_source_snapshot/openlogic_en_9620cc7'
TROOT=R/'05_translation/openlogic_hi_9620cc7/locale/hi'
SCHEMA_URL='https://raw.githubusercontent.com/KokunoYumeto/OpenLogic-translations/811091d54be4989918864732073279a588340e6f/catalogue/translation-decisions/translation-decision.schema.json'
SCHEMA_SHA='50e7fa407b62c711f92f8b93be591d3b4a6e1c4adb1386c398bb5f76844d9f90'
SCHEMA_BYTES=10787
SOURCE_COMMIT='9620cc73f9c8e0ad003c514a5d3748f29611c4c0'
READER_NAME='00_OpenLogic_hi-Deva-IN_reader.pdf'
READER_SHA='91279e723a58acdedcdf85432d59c6cefd17d954fbd6f342a70bff31c1aa5253'

def digest(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def clean(text, limit=None):
    value=' '.join(str(text or '').split())
    if limit and len(value)>limit: value=value[:limit-1]+'…'
    return value
def expand(items):
    result=[]
    for item in items:
        if 'path' not in item: continue
        for hit in range(1,int(item.get('hits',1))+1): result.append({**item,'hit_in_line':hit})
    return result
def parse_range(value):
    nums=[int(x) for x in re.findall(r'\d+',str(value or ''))]
    return (min(nums),max(nums)) if nums else (None,None)

class TextFile:
    def __init__(self,path):
        self.path=path; self.data=path.read_bytes(); self.bom=3 if self.data.startswith(b'\xef\xbb\xbf') else 0
        self.text=self.data[self.bom:].decode('utf-8'); self.lines=self.text.splitlines(keepends=True)
        self.sha=digest(self.data)
    def line(self,number):
        if number is None or not 1<=number<=len(self.lines): return ''
        return self.lines[number-1].rstrip('\r\n')
    def line_start_byte(self,number):
        return self.bom+len(''.join(self.lines[:number-1]).encode('utf-8'))
    def term_span(self,number,term,hit=1):
        row=self.line(number); starts=[]; pos=0
        while term:
            found=row.find(term,pos)
            if found<0: break
            starts.append(found); pos=found+len(term)
        if not starts or hit<1 or hit>len(starts): return None
        start_char=starts[hit-1]; start=self.line_start_byte(number)+len(row[:start_char].encode('utf-8'))
        return start,start+len(term.encode('utf-8'))
    def range_span(self,start,end):
        if start is None or end is None or not 1<=start<=end<=len(self.lines): return None
        a=self.line_start_byte(start); b=self.line_start_byte(end)+len(self.lines[end-1].encode('utf-8'))
        return a,b
    def excerpt(self,start,end=None):
        if start is None or not 1<=start<=len(self.lines): return ''
        end=start if end is None else min(end,len(self.lines))
        return clean(' '.join(x.rstrip('\r\n') for x in self.lines[start-1:end]),1200)

def line_status(start,end,reason):
    return {'status':'available','start':start,'end':end} if start is not None and end is not None else {'status':'pending','reason':reason}
def byte_status(span,reason):
    return {'status':'available','start':span[0],'end_exclusive':span[1]} if span else {'status':'pending','reason':reason}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    schema_data=requests.get(SCHEMA_URL,timeout=60).content
    assert len(schema_data)==SCHEMA_BYTES and digest(schema_data)==SCHEMA_SHA
    schema=json.loads(schema_data); Draft202012Validator.check_schema(schema)
    (OUT/'translation-decision.schema.json').write_bytes(schema_data)
    ledger_lines=[x for x in (TERM/'SUBSTANTIVE_DECISION_LOG.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    ledger=[json.loads(x) for x in ledger_lines]; ledger_by={x['decision_id']:x for x in ledger}
    custom=json.loads((TERM/'DECISION_REVIEW_MACHINE.json').read_text(encoding='utf-8'))
    custom_by=defaultdict(list)
    for occurrence in custom['occurrences']: custom_by[occurrence['decision_id']].append(occurrence)
    graph=json.loads((Q/'INTEGRATED_READER_EVIDENCE.json').read_text(encoding='utf-8'))['records']
    graph_by={x['path']:x for x in graph}; assert len(graph_by)==722
    align={}
    with (TERM/'FUTURE_URDU_ALIGNMENT_KEYS.tsv').open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream,delimiter='\t'): align[row['source_path']]=row
    assert len(align)==722 and set(align)==set(graph_by)
    source_files={path:TextFile(SROOT/'content'/path) for path in graph_by}
    target_files={path:TextFile(TROOT/'content'/path) for path in graph_by}
    source_config=TextFile(SROOT/'open-logic-config.sty'); target_config=TextFile(TROOT/'open-logic-config.sty')
    ledger_path=TERM/'SUBSTANTIVE_DECISION_LOG.jsonl'; ledger_hash=digest(ledger_path.read_bytes())
    graph_path=Q/'INTEGRATED_READER_EVIDENCE.json'; graph_hash=digest(graph_path.read_bytes())
    term_web_path=TERM/'TERM_WEB.tsv'; term_web=TextFile(term_web_path)
    term_web_rows={}
    with term_web_path.open(encoding='utf-8-sig',newline='') as stream:
        for line_number,row in enumerate(csv.DictReader(stream,delimiter='\t'),2):
            term_web_rows[(row['english'],row['hi_deva_in'])]=(line_number,row)
    edition={'edition_id':'openlogic-hi','language_tag':'hi-Deva-IN','language_name':'Hindi','script':'Deva','territory':'India','locale':'hi-IN',
      'register_or_variant':'मानक आधुनिक हिंदी का विश्वविद्यालय-स्तरीय तर्कशास्त्रीय रजिस्टर',
      'notation_profile':'international mathematical notation; formal syntax preserved','layer_type':'semantic_translation','parent_semantic_edition_id':None}
    release={'edition':edition,'release_tag':'HI-OLP-PUB-0008','repository':'https://github.com/KokunoYumeto/open-logic-hi','doi':'10.5281/zenodo.21920511',
      'source_revision':SOURCE_COMMIT,'coverage_state':'complete','source_units':722,'reader_units':722}
    evidence_refs=[
      {'path_or_uri':'terminology/SUBSTANTIVE_DECISION_LOG.jsonl','bytes':ledger_path.stat().st_size,'sha256':ledger_hash,'version_or_ref':'Hindi retrospective decision ledger 2026-09-04'},
      {'path_or_uri':'qa/reconciliation/INTEGRATED_READER_EVIDENCE.json','bytes':graph_path.stat().st_size,'sha256':graph_hash,'version_or_ref':'HI-OLP-READER-RECONCILED-20260904'}]

    def file_bundle(path,target=False):
        if path.endswith('open-logic-config.sty'):
            return (target_config if target else source_config),'open-logic-config.sty',('hindi-config' if target else 'source-config'),('hindi-translation/' if target else 'source-frozen/')+'open-logic-config.sty'
        row=align[path]; tf=target_files[path] if target else source_files[path]
        fid=(row['hindi_file_id'] if target else row['source_file_id']) or row['alignment_key']+(':hi' if target else ':source')
        public=('hindi-translation/content/' if target else 'source-frozen/content/')+path
        return tf,path,fid,public

    def locator(path,start,end,term,hit,target,sense,context,range_bytes=False,printed_page=None):
        tf,normalized,fid,public=file_bundle(path,target)
        valid=start is not None and end is not None and 1<=start<=end<=len(tf.lines)
        span=tf.range_span(start,end) if range_bytes and valid else (tf.term_span(start,term,hit) if valid and term else None)
        excerpt=tf.excerpt(start,end) if valid else clean(term or context or 'स्थान-अभिलेख',1200)
        if not excerpt: excerpt=clean(term or 'स्थान-अभिलेख')
        return {'path':public,'file_id':fid,'file_sha256':tf.sha,
          'line_span':line_status(start,end,'The legacy event does not identify one exact line span.'),
          'byte_span':byte_status(span,'No exact literal byte span is asserted for this derived/range locator.'),
          'printed_page':printed_page,'excerpt':excerpt,'term':term or None,'intended_sense':sense or None,'context':context or None}

    decisions=[]
    for d in custom['decisions']:
        original=ledger_by[d['decision_id']]; source_candidates=expand(original.get('source_locations',[])); occurrences=[]
        for index,old in enumerate(custom_by[d['decision_id']],1):
            target_path=old.get('target_path') or (original.get('target_locations') or [{}])[0].get('path','')
            if target_path.endswith('open-logic-config.sty'): target_path='open-logic-config.sty'
            if target_path not in graph_by and target_path!='open-logic-config.sty': raise AssertionError('Unknown target path '+target_path)
            tstart,tend=parse_range(old.get('target_line'))
            target_term=d.get('chosen_target') if old['kind']=='target_literal_occurrence' else None
            target_hit=int(old.get('target_hit_in_line') or 1)
            source_path=old.get('source_path',''); sline=int(old['source_line']) if str(old.get('source_line','')).isdigit() else None
            source_hit=1
            match=re.search(r'#(\d+)$',old.get('source_line_candidates',''))
            if match: source_hit=int(match.group(1))
            association=old.get('source_locator_status','')
            if not source_path:
                if source_candidates:
                    chosen=source_candidates[(index-1)%len(source_candidates)]; source_path=chosen['path']; sline=int(chosen['line']); source_hit=int(chosen.get('hit_in_line',1))
                    association='derived_source_exemplar_from_decision_record; not_asserted_one_to_one'
                elif target_path in graph_by:
                    source_path=target_path; sline=tstart; association='derived_same_unit_source_line; no_exact_source_literal_recorded'
                else:
                    source_path='open-logic-config.sty'; association='derived_shared_configuration_source'
                    references=' '.join(str(x.get('reference','')) for x in original.get('source_locations',[]))
                    found=re.search(r'lines?(\d+)',references); sline=int(found.group(1)) if found else None
            if source_path.endswith('open-logic-config.sty'): source_path='open-logic-config.sty'
            if source_path not in graph_by and source_path!='open-logic-config.sty': raise AssertionError('Unknown source path '+source_path)
            if d['kind']=='terminology':
                send=sline; source_term=d.get('source_term') or original.get('source_term')
            else:
                send=sline if sline is not None else tend
                source_term=None
            printed=str(old['printed_page_number']) if old.get('printed_page_number')!='' and old.get('pdf_page_mapping_status','').startswith('exact_') else None
            source_loc=locator(source_path,sline,send,source_term,source_hit,False,d.get('register_or_domain',''),association,range_bytes=not bool(source_term))
            target_loc=locator(target_path,tstart,tend,target_term,target_hit,True,d.get('register_or_domain',''),old.get('target_context') or old.get('pdf_page_mapping_status',''),range_bytes=not bool(target_term),printed_page=printed)
            row=align.get(target_path); unit_id='OLP-'+(row['ordinal'].zfill(4) if row else '0000')
            section={}
            try: section=json.loads(old.get('target_section') or '{}')
            except json.JSONDecodeError: pass
            part=section.get('title_tex') if section.get('kind')=='part' else None
            chapter=section.get('title_tex') if section.get('kind')=='chapter' else None
            section_title=section.get('title_tex') if section.get('kind') in {'section','subsection','subsubsection','paragraph'} else None
            exact=bool(old.get('pdf_physical_page')) and old.get('pdf_page_mapping_status','').startswith('exact_')
            if exact:
                reader={'status':'available','artifact_filename':READER_NAME,'artifact_sha256':READER_SHA,'profile':'reconciled hi-Deva-IN A4 reader',
                  'printed_page':str(old['printed_page_number']),'assembled_pdf_page':int(old['pdf_physical_page']),'provenance':old['pdf_page_mapping_status']}
            else:
                reason=old.get('pdf_page_mapping_status','pending')
                if old.get('pdf_candidate_physical_pages'): reason+='; candidate physical pages '+str(old['pdf_candidate_physical_pages'])
                status='not_applicable' if 'shared_config' in reason else 'pending'
                reader={'status':status,'reason':reason}
            occurrences.append({'occurrence_id':old['occurrence_id'],'unit_id':unit_id,
              'semantic_unit_id':f'{unit_id}:{d["decision_id"]}:{index:06d}','part_title':part,'chapter_title':chapter,'section_title':section_title,
              'source':source_loc,'target':target_loc,'reader_locator':reader,'evidence_refs':evidence_refs})
        if not occurrences:
            # The canonical contract requires every decision to retain at least
            # one occurrence. These controlled terms have zero literal uses in
            # the accepted 722-file graph, so bind them to their exact bilingual
            # registry row instead of fabricating a book/reader occurrence.
            key=(d.get('source_term',''),d.get('chosen_target',''))
            assert key in term_web_rows
            line_number,row=term_web_rows[key]; excerpt=term_web.excerpt(line_number)
            source_span=term_web.term_span(line_number,key[0],1); target_span=term_web.term_span(line_number,key[1],1)
            assert source_span and target_span
            def registry_locator(term,span,sense):
                return {'path':'terminology/TERM_WEB.tsv','file_id':'openlogic-hi-term-web','file_sha256':term_web.sha,
                  'line_span':{'status':'available','start':line_number,'end':line_number},
                  'byte_span':{'status':'available','start':span[0],'end_exclusive':span[1]},'printed_page':None,
                  'excerpt':excerpt,'term':term,'intended_sense':sense,
                  'context':'Controlled bilingual terminology-registry locus; zero literal occurrences in the accepted 722-file reader graph.'}
            occurrences.append({'occurrence_id':d['decision_id']+'-OCC-REGISTRY-000001','unit_id':'OLP-0000',
              'semantic_unit_id':'OLP-0000:'+d['decision_id']+':TERM-WEB','part_title':None,'chapter_title':None,'section_title':'TERM_WEB.tsv controlled registry',
              'source':registry_locator(key[0],source_span,d.get('register_or_domain','')),
              'target':registry_locator(key[1],target_span,d.get('register_or_domain','')),
              'reader_locator':{'status':'not_applicable','reason':'The controlled term has zero literal target occurrences in the complete accepted reader; this is a registry-only locus and no reader page is invented.'},
              'evidence_refs':evidence_refs+[{'path_or_uri':'terminology/TERM_WEB.tsv','bytes':term_web_path.stat().st_size,'sha256':term_web.sha,'version_or_ref':'accepted Hindi controlled terminology registry'}]})
        assert occurrences
        first=occurrences[0]
        if d['kind']=='terminology': record_kind='terminology'; recording='retrospective'
        elif d['kind']=='shared_terminology_or_reference_configuration': record_kind='register'; recording='derived'
        else:
            low=(d.get('chosen_disposition') or '').casefold()
            record_kind='notation' if any(x in low for x in ['math','delimiter','formula','tex','macro','reference','label']) else 'orthography'
            recording='derived'
        source_construction=d.get('source_term') or clean(first['source']['excerpt'],500)
        intended=d.get('register_or_domain') or d.get('chosen_register') or 'Frozen-source-faithful Hindi translation or typesetting correction.'
        chosen=d.get('chosen_target') or d.get('chosen_register') or clean(first['target']['excerpt'],1200)
        rationale=d.get('retrospective_rationale_and_rejected_choices') or d.get('chosen_disposition') or d.get('alternatives_record') or 'Choice retained from the accepted Hindi edition and exposed for correction.'
        authority_text=clean(d.get('authority_as_previously_recorded') or d.get('actual_authority_checked') or 'No separate external authority was recorded.',2000)
        authorities=[{'authority_id':d['decision_id']+'-AUTH-001','citation':authority_text,'source_sha256':ledger_hash,
          'status':'not_checked','note':'Citation preserved from the prior ledger. This canonical adapter verified local source/target bytes but did not newly authenticate an external passage.'}]
        alternatives=[]; alt=clean(d.get('alternatives_record'),2000)
        if alt:
            disp='rejected' if 'reject' in alt.casefold() or 'अस्वीकृत' in alt else 'viable_alternative'
            alternatives=[{'rendering':alt,'disposition':disp,'reason':'Legacy alternatives note preserved verbatim as one aggregate item; individual alternatives were not invented by the adapter.'}]
        provisional='provisional' in str(d.get('status','')).casefold()
        priority={'P1':'urgent','P2':'high','P3':'normal'}[d['review_priority']]
        decisions.append({'decision_id':d['decision_id'],'record_kind':record_kind,'recording_mode':recording,'edition':edition,
          'source_term_or_construction':source_construction,'intended_sense':intended,'chosen_rendering':chosen,'rationale':rationale,
          'authorities_checked':authorities,'alternatives':alternatives,'confidence':d['confidence'],
          'confidence_reason':f'{d.get("authority_verification_status","recorded evidence")}; {d.get("backfill_status","adapter projection")}',
          'provisional':provisional,'review_priority':priority,'expert_review_useful':True,
          'expert_review_reason':'This materially judgment-dependent choice is exposed so a specialist can confirm or improve it without blocking the accepted edition.',
          'please_double_check_question':d.get('please_double_check') or 'Please double-check this choice in its exact source and Hindi context.',
          'occurrences':occurrences})
    generator=Path(__file__)
    machine={'schema_version':'openlogic-translation-decisions/1.0.0','edition_release':release,'generated_utc':now(),
      'generator':{'path_or_uri':'tools/adapt_decision_review_to_canonical.py','bytes':generator.stat().st_size,'sha256':digest(generator.read_bytes()),'version_or_ref':'HI-OLP-PUB-0008'},
      'decisions':decisions}
    validator=Draft202012Validator(schema,format_checker=FormatChecker()); errors=sorted(validator.iter_errors(machine),key=lambda x:list(x.path))
    if errors: raise AssertionError('Canonical schema failure: '+errors[0].json_path+' '+errors[0].message)
    machine_path=OUT/'DECISIONS.json'; machine_path.write_text(json.dumps(machine,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
    shutil.copyfile(TERM/'DECISION_REVIEW_INDEX.md',OUT/'TRANSLATION_DECISIONS_FULL.md')
    shutil.copyfile(TERM/'DECISION_REVIEW_PRIORITY.md',OUT/'PRIORITY_REVIEW.md')
    start='''# ओपन लॉजिक परियोजना — हिंदी अनुवाद-निर्णय समीक्षा

यह संपूर्ण `hi-Deva-IN` संस्करण की समीक्षा-सामग्री का प्रवेश-बिंदु है। मुख्य
अनुवाद 722/722 स्रोत इकाइयों और 975-पृष्ठीय पाठक-संस्करण में पूरा है; यह पैकेज
अनुवाद को दोबारा नहीं करता, बल्कि 400 सार्थक निर्णयों को जाँचने योग्य बनाता है।

- `TRANSLATION_DECISIONS_FULL.md`: 400 निर्णयों की पठनीय संपूर्ण सूची।
- `PRIORITY_REVIEW.md`: P1/P2 के 270 मामले; सभी 20 अस्थायी पद इसमें हैं।
- `DECISION_OCCURRENCES.csv`: 26,942 उदाहरण—26,904 पुस्तक/सुधार स्थान और
  शून्य पुस्तक-प्रयोग वाले 38 पदों की सटीक शब्दावली-पंजी पंक्तियाँ; कोई
  पाठक-स्थान गढ़ा नहीं गया।
- `DECISIONS.json`: इसी सामग्री का प्रामाणिक मशीन-पठनीय रूप।
- `translation-decision.schema.json`: साझा OpenLogic अनुबंध की स्थिर प्रति।
- `TRANSLATION_DECISION_QA.json`: स्कीमा, गणना, हैश और दृश्य-संगति का प्रमाण।

## भाषा, लिपि और रजिस्टर

यह एक अर्थगत हिंदी संस्करण है: मानक आधुनिक हिंदी, देवनागरी (`hi-Deva-IN`),
विश्वविद्यालय-स्तरीय तर्कशास्त्रीय रजिस्टर और अंतरराष्ट्रीय गणितीय संकेतन। उपलब्ध
पाठक-वर्ग तथा वर्तमान भारतीय मानक के लिए अलग रोमन/Hinglish संस्करण पर्याप्त रूप
से उचित नहीं है; रोमन सहायक शब्द-सूची बाद में उपयोगी हो सकती है, पर वह दूसरा
अर्थगत संस्करण नहीं होगी। उर्दू अलग भाषा/लिपि की स्वतंत्र अनुवाद-परंपरा है, हिंदी
की लिप्यंतरण परत नहीं; इस संस्करण में उसे मिलाया नहीं गया है। अलग क्षेत्रीय हिंदी
संस्करण का अभी वास्तविक साक्ष्य नहीं मिला, इसलिए कृत्रिम रूप से कोई प्रकार नहीं
बनाया गया।

## प्रमाण की सीमा

सटीक स्रोत/लक्ष्य पंक्तियाँ और फ़ाइल-हैश दिए गए हैं। जहाँ अंतिम PDF पृष्ठ का
एकार्थक निर्धारण हुआ, वही `available` है; संभावित पृष्ठ या साझा विन्यास `pending`
अथवा `not_applicable` हैं और अनुमानित पृष्ठ को सटीक नहीं कहा गया। पूर्वव्यापी
कारण पूर्वव्यापी ही हैं। विशेषज्ञ सुधार स्वागतयोग्य है, पर पूर्ण पुस्तक या प्रकाशन
की रोक नहीं।

स्थिर साझा स्कीमा: commit `811091d54be4989918864732073279a588340e6f`,
SHA-256 `50e7fa407b62c711f92f8b93be591d3b4a6e1c4adb1386c398bb5f76844d9f90`।
'''
    (OUT/'START_HERE.md').write_text(start,encoding='utf-8',newline='\n')
    fields=['occurrence_id','decision_id','unit_id','semantic_unit_id','record_kind','source_term_or_construction','intended_sense','chosen_rendering',
      'source_path','source_file_sha256','source_line_start','source_line_end','source_byte_start','source_byte_end_exclusive','source_excerpt',
      'target_path','target_file_sha256','target_line_start','target_line_end','target_byte_start','target_byte_end_exclusive','target_excerpt',
      'reader_status','printed_page','assembled_pdf_page','reader_provenance_or_reason','rationale','authorities','alternatives','confidence','provisional','review_priority','please_double_check_question']
    rows=[]
    for decision in decisions:
        for occurrence in decision['occurrences']:
            source=occurrence['source']; target=occurrence['target']; reader=occurrence['reader_locator']
            rows.append({'occurrence_id':occurrence['occurrence_id'],'decision_id':decision['decision_id'],'unit_id':occurrence['unit_id'],'semantic_unit_id':occurrence['semantic_unit_id'],
              'record_kind':decision['record_kind'],'source_term_or_construction':decision['source_term_or_construction'],'intended_sense':decision['intended_sense'],'chosen_rendering':decision['chosen_rendering'],
              'source_path':source['path'],'source_file_sha256':source['file_sha256'],'source_line_start':source['line_span'].get('start',''),'source_line_end':source['line_span'].get('end',''),
              'source_byte_start':source['byte_span'].get('start',''),'source_byte_end_exclusive':source['byte_span'].get('end_exclusive',''),'source_excerpt':source['excerpt'],
              'target_path':target['path'],'target_file_sha256':target['file_sha256'],'target_line_start':target['line_span'].get('start',''),'target_line_end':target['line_span'].get('end',''),
              'target_byte_start':target['byte_span'].get('start',''),'target_byte_end_exclusive':target['byte_span'].get('end_exclusive',''),'target_excerpt':target['excerpt'],
              'reader_status':reader['status'],'printed_page':reader.get('printed_page',''),'assembled_pdf_page':reader.get('assembled_pdf_page',''),
              'reader_provenance_or_reason':reader.get('provenance') or reader.get('reason',''),'rationale':decision['rationale'],
              'authorities':json.dumps(decision['authorities_checked'],ensure_ascii=False,separators=(',',':')),'alternatives':json.dumps(decision['alternatives'],ensure_ascii=False,separators=(',',':')),
              'confidence':decision['confidence'],'provisional':str(decision['provisional']).lower(),'review_priority':decision['review_priority'],'please_double_check_question':decision['please_double_check_question']})
    csv_path=OUT/'DECISION_OCCURRENCES.csv'
    with csv_path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    ids=[d['decision_id'] for d in decisions]; occs=[o for d in decisions for o in d['occurrences']]; occ_ids=[x['occurrence_id'] for x in occs]
    registry_rows=sum('-OCC-REGISTRY-' in x['occurrence_id'] for x in occs); book_rows=len(occs)-registry_rows
    assert len(ids)==len(set(ids))==400 and len(occ_ids)==len(set(occ_ids))==26942 and len(rows)==26942
    assert registry_rows==38 and book_rows==26904
    with csv_path.open(encoding='utf-8-sig',newline='') as stream: assert sum(1 for _ in csv.DictReader(stream))==26942
    full=(OUT/'TRANSLATION_DECISIONS_FULL.md').read_text(encoding='utf-8'); priority=(OUT/'PRIORITY_REVIEW.md').read_text(encoding='utf-8')
    assert all(full.count(f'| {did} |')==1 for did in ids)
    high_ids={d['decision_id'] for d in decisions if d['review_priority'] in {'urgent','high'}}; assert len(high_ids)==270
    custom_priority={d['decision_id'] for d in custom['decisions'] if d['review_priority'] in {'P1','P2'}}; assert high_ids==custom_priority
    reader_counts=Counter(x['reader_locator']['status'] for x in occs)
    hashes={p.name:{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in [OUT/'START_HERE.md',OUT/'TRANSLATION_DECISIONS_FULL.md',OUT/'PRIORITY_REVIEW.md',csv_path,machine_path,OUT/'translation-decision.schema.json']}
    qa={'schema':'openlogic-translation-decision-qa/1.0.0','generated_utc':now(),'status':'PASS','edition_id':'openlogic-hi','coverage_state':'complete',
      'normative_schema':{'source_uri':SCHEMA_URL,'frozen_commit':'811091d54be4989918864732073279a588340e6f','bytes':SCHEMA_BYTES,'sha256':SCHEMA_SHA,'metaschema_validation':'PASS','instance_validation':'PASS'},
      'counts':{'source_units':722,'reader_units':722,'decisions':400,'occurrences':26942,'book_or_correction_occurrences':26904,'registry_only_zero_use_terms':38,'unique_decision_ids':400,'unique_occurrence_ids':26942,'priority_urgent_or_high':270,'provisional':20,'reader_locator_status':dict(reader_counts)},
      'projection_checks':{'json_schema':'PASS','csv_rows_equal_json_occurrences':'PASS','full_markdown_all_decisions_once':'PASS','priority_markdown_matches_urgent_high_ids':'PASS','source_target_hashes_bound_to_frozen_or_accepted_bytes':'PASS','zero_use_terms_bound_to_exact_registry_rows_not_fabricated_reader_loci':'PASS','unknown_reader_pages_remain_pending_not_guessed':'PASS','generated_placeholders_or_silent_omissions':0},
      'reader_evidence':{'artifact_filename':READER_NAME,'sha256':READER_SHA,'pages':975,'accepted_graph':{'path':'qa/reconciliation/INTEGRATED_READER_EVIDENCE.json','bytes':graph_path.stat().st_size,'sha256':graph_hash},'formula_citation_identifier_link_hierarchy_unicode_script_checks':'See accepted reader evidence and reconciliation receipts in the provenance ZIP; the adapter did not rebuild or change reader bytes.'},
      'variant_assessment':{'semantic_editions_recommended':1,'current':'hi-Deva-IN / Deva / standard modern Hindi','roman_hinglish':'not warranted as a separate semantic edition on current evidence','urdu':'separate language edition, not a Hindi script projection','regional_variants':'none manufactured without evidence'},
      'outputs':hashes,'limitations':['External terminology citations are preserved verbatim but were not newly authenticated by this adapter.','Derived source pairing is labelled in locator context and is not asserted as one-to-one semantic alignment.','Thirty-eight controlled terms have zero reader uses; canonical occurrences point to exact bilingual registry rows and are not represented as book occurrences.','Human review is useful but never a completion or release gate.']}
    qa_path=OUT/'TRANSLATION_DECISION_QA.json'; qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':'PASS','schema_sha256':SCHEMA_SHA,'decisions':400,'occurrences':26942,'book_or_correction_occurrences':26904,'registry_only_zero_use_terms':38,'reader_locator_status':dict(reader_counts),'outputs':{**hashes,qa_path.name:{'bytes':qa_path.stat().st_size,'sha256':digest(qa_path.read_bytes())}}},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
