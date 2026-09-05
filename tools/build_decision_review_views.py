"""Build interoperable review views for the completed Hindi Open Logic reader.

Inputs are bounded to the existing 400-decision ledger, accepted 722-record
graph, frozen source/target files named by that graph, and final PDF extraction.
The script never edits translation/PDF bytes and never claims fuzzy page
matches as exact.
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import csv, hashlib, json, re, unicodedata

R=Path(__file__).resolve().parents[1]
TERM=R/'04_terminology'
Q=R/'07_qa/openlogic/HI-OLP-READER-RECONCILED-20260904'
S=R/'02_source_snapshot/openlogic_en_9620cc7/content'
T=R/'05_translation/openlogic_hi_9620cc7/locale/hi/content'
PDF=R/'06_build/openlogic_hi_9620cc7/HI-OLP-READER-RECONCILED-20260904/open-logic-complete-hi-reconciled.pdf'
CONFIG=T.parent/'open-logic-config.sty'
OUT_JSON=TERM/'DECISION_REVIEW_MACHINE.json'
OUT_CSV=TERM/'DECISION_OCCURRENCES.csv'
OUT_FULL=TERM/'DECISION_REVIEW_INDEX.md'
OUT_PRIORITY=TERM/'DECISION_REVIEW_PRIORITY.md'
OUT_SCHEMA=TERM/'DECISION_REVIEW_SCHEMA.json'
OUT_RECEIPT=TERM/'DECISION_REVIEW_RECEIPT.json'
SCHEMA_VERSION='openlogic-translation-decision-review/1.0.0'
SOURCE_COMMIT='9620cc73f9c8e0ad003c514a5d3748f29611c4c0'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s or '').split())
def short(s,n=260):
    s=norm(s);return s if len(s)<=n else s[:n-1]+'…'
def load_json(path):return json.loads(path.read_text(encoding='utf-8'))
def md(s):return str(s or '').replace('|','\\|').replace('\n',' ')
def expand_locs(items):
    out=[]
    for item in items:
        for hit in range(1,int(item.get('hits',1))+1):out.append({**item,'hit_in_line':hit})
    return out
def page_runs(values):
    values=sorted(set(int(x) for x in values))
    if not values:return ''
    runs=[];start=prev=values[0]
    for value in values[1:]:
        if value==prev+1:prev=value;continue
        runs.append(str(start) if start==prev else f'{start}-{prev}');start=prev=value
    runs.append(str(start) if start==prev else f'{start}-{prev}')
    return ','.join(runs)
def section_at(text,line):
    rx=re.compile(r'\\(part|chapter|section|subsection|subsubsection|paragraph)\*?(?:\[[^]]*\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}')
    found=[]
    for i,row in enumerate(text.splitlines(),1):
        if i>line:break
        for m in rx.finditer(row):found.append({'kind':m.group(1),'title_tex':short(m.group(2),180),'line':i})
    return found[-1] if found else {'kind':'file','title_tex':'','line':1}
def authority_status(authority):
    low=(authority or '').casefold()
    if any(x in low for x in ['not independently rechecked','no separate source locator','not found','not located','no direct']):
        return 'recorded_but_not_independently_rechecked_or_not_found'
    if any(x in low for x in ['cstt','ncert','iit','azim premji','source comparison','exact english source','build','rendered']):
        return 'specific_authority_or_deterministic_evidence_previously_checked'
    return 'previously_recorded_rationale_not_rechecked_in_this_backfill'
def confidence(decision):
    if decision['kind']=='terminology':
        if 'provisional' in decision.get('status','').casefold():return 'medium'
        if decision.get('target_literal_hits',0)==0:return 'medium'
        if authority_status(decision.get('authority_as_previously_recorded','')).startswith('specific_'):return 'high'
        return 'medium'
    reason=(decision.get('chosen_disposition') or '').casefold()
    if any(x in reason for x in ['source', 'translation', 'reference', 'iff', 'rationale']):return 'medium'
    return 'high'
def priority(decision,conf):
    if decision['kind']=='terminology' and 'provisional' in decision.get('status','').casefold():return 'P1'
    if decision.get('event_chain_gaps') or conf!='high':return 'P2'
    return 'P3'

def main():
    base=[json.loads(row) for row in (TERM/'SUBSTANTIVE_DECISION_LOG.jsonl').read_text(encoding='utf-8').splitlines() if row.strip()]
    assert len(base)==len({d['decision_id'] for d in base})==400
    graph=load_json(Q/'INTEGRATED_READER_EVIDENCE.json')['records'];assert len(graph)==722
    bypath={r['path']:r for r in graph}
    source_cache={p:(S/p).read_text(encoding='utf-8-sig') for p in bypath}
    target_cache={p:(T/p).read_text(encoding='utf-8-sig') for p in bypath}
    target_cache['open-logic-config.sty']=CONFIG.read_text(encoding='utf-8-sig')
    page_text=(Q/'EXTRACTED_READER.txt').read_text(encoding='utf-8').split('\f')
    if page_text and not page_text[-1].strip():page_text.pop()
    assert len(page_text)==975
    page_norm=[norm(x) for x in page_text]
    starts=sorted({int(r['tex_entry_page_counter']) for r in graph if r.get('tex_entry_page_counter') is not None})
    def page_range(path):
        if path not in bypath:return []
        start=int(bypath[path]['tex_entry_page_counter'])
        higher=[x for x in starts if x>start]
        end=(higher[0] if higher else 974)
        # TeX counter N corresponds to physical PDF page N+1 in this reader.
        return list(range(max(1,start+1),min(975,end+1)+1))
    def term_hits(term,pages):
        needle=norm(term)
        if not needle:return []
        hits=[]
        for physical in pages:
            count=page_norm[physical-1].count(needle)
            hits.extend([physical]*count)
        return hits
    def context_page(path,line_no,term,hit_in_line,pages):
        if path not in target_cache or not pages:return None
        lines=target_cache[path].splitlines();line=lines[line_no-1]
        # Probe around this literal with Hindi lexical context. TeX commands and
        # punctuation are separators; braced reader text remains.
        positions=[m.start() for m in re.finditer(re.escape(term),line)] if term else []
        anchor=positions[min(hit_in_line-1,len(positions)-1)] if positions else len(line)//2
        left=line[:anchor];right=line[anchor+len(term):]
        lt=re.findall(r'[\u0900-\u097F][\u0900-\u097F\u200c\u200d़ँंःािीुूृॄेैोौ्]*',left)
        rt=re.findall(r'[\u0900-\u097F][\u0900-\u097F\u200c\u200d़ँंःािीुूृॄेैोौ्]*',right)
        center=re.findall(r'[\u0900-\u097F][\u0900-\u097F\u200c\u200d़ँंःािीुूृॄेैोौ्]*',term)
        tokens=(lt[-5:]+center+rt[:5])
        probes=[]
        for width in range(min(7,len(tokens)),2,-1):
            for start in range(max(1,len(tokens)-width+1)):
                probes.append(' '.join(tokens[start:start+width]))
        for probe in probes:
            matched=[p for p in pages if probe and probe in page_norm[p-1]]
            if len(matched)==1:return matched[0]
        # Fall back to surrounding source lines when TeX splits a prose phrase.
        block=' '.join(lines[max(0,line_no-2):min(len(lines),line_no+1)])
        words=re.findall(r'[\u0900-\u097F][\u0900-\u097F\u200c\u200d़ँंःािीुूृॄेैोौ्]*',block)
        for width in range(min(7,len(words)),3,-1):
            probe=' '.join(words[:width]);matched=[p for p in pages if probe in page_norm[p-1]]
            if len(matched)==1:return matched[0]
        return None
    decisions=[];occurrences=[]
    for original in base:
        d=dict(original);conf=confidence(d);prio=priority(d,conf)
        d.update(schema_version=SCHEMA_VERSION,target_locale='hi-Deva-IN',target_script='Devanagari',target_region='India',
          source_repository='OpenLogicProject/OpenLogic',source_commit=SOURCE_COMMIT,confidence=conf,review_priority=prio,
          reversible=True,human_review_is_release_gate=False)
        auth=d.get('authority_as_previously_recorded') or d.get('actual_authority_checked') or d.get('source_locations')
        d['authority_verification_status']=authority_status(str(auth))
        d['please_double_check']=d.pop('precise_review_question', 'Please double-check this choice against its exact context and a citable Hindi scholarly source.')
        if d['kind']=='terminology':
            targets=defaultdict(list)
            for loc in expand_locs(d.get('target_locations',[])):targets[loc['path']].append(loc)
            sources=defaultdict(list)
            all_sources=expand_locs(d.get('source_locations',[]))
            for loc in all_sources:sources[loc['path']].append(loc)
            for path,locs in targets.items():
                locs=sorted(locs,key=lambda x:x['line']);pages=page_range(path)
                expanded=term_hits(d['chosen_target'],pages)
                exact_page_sequence=len(expanded)==len(locs) and len(locs)>0
                src_same=sorted(sources.get(path,[]),key=lambda x:(int(x['line']),int(x.get('hit_in_line',1))))
                exact_source_sequence=len(src_same)==len(locs) and len(locs)>0
                for index,loc in enumerate(locs):
                    tline=int(loc['line'])
                    if exact_source_sequence:
                        paired=src_same[index]
                        source_status='exact_same_file_sequence_pair'
                    elif src_same:
                        # Source and target retain the same TeX structure closely.
                        # Select the nearest exact source-literal line, while
                        # labelling the cross-language pairing as inferred.
                        paired=min(src_same,key=lambda x:(abs(int(x['line'])-tline),abs(int(x.get('hit_in_line',1))-int(loc.get('hit_in_line',1)))))
                        source_status='nearest_same_file_literal_candidate; pairing_inferred'
                    else:
                        paired=None
                        source_status='decision_record_source_locations; no_same_file_literal_candidate'
                    physical=context_page(path,tline,d['chosen_target'],int(loc.get('hit_in_line',1)),pages)
                    if physical is None and exact_page_sequence:physical=expanded[index]
                    matched=sorted(set(expanded))
                    mapping=('exact_unique_context_in_final_pdf_extraction' if physical and not exact_page_sequence else
                      ('exact_literal_sequence_within_file_page_range' if physical else
                       ('candidate_pages_from_exact_term_hits' if matched else 'no_exact_pdf_extraction_match; file_page_range_only')))
                    source_path=paired['path'] if paired else ''
                    source_section=(section_at(source_cache[source_path],int(paired['line'])) if paired and source_path in source_cache else {})
                    source_reference=(f"{source_path}:{paired['line']}#{paired.get('hit_in_line',1)}" if paired else
                      f"decision:{d['decision_id']}.source_locations")
                    occurrence={
                      'schema_version':SCHEMA_VERSION,'occurrence_id':f"{d['decision_id']}-OCC-{len(occurrences)+1:06d}",'decision_id':d['decision_id'],
                      'kind':'target_literal_occurrence','source_term':d['source_term'],'source_sense_or_domain':d.get('register_or_domain',''),
                      'source_unit_id':(bypath[source_path].get('source_id') or source_path) if source_path else '',
                      'source_path':source_path,'source_line':paired['line'] if paired else '',
                      'source_line_candidates':source_reference,'source_candidate_count':len(src_same) if src_same else len(all_sources),
                      'source_locator_status':source_status,
                      'source_section':json.dumps(source_section,ensure_ascii=False,separators=(',',':')),
                      'target_unit_id':(bypath[path].get('target_id') or path) if path in bypath else 'locale-config',
                      'target_path':path,'target_line':tline,'target_hit_in_line':loc.get('hit_in_line',1),'target_section':json.dumps(section_at(target_cache[path],tline),ensure_ascii=False,separators=(',',':')),
                      'chosen_rendering':d['chosen_target'],'target_locale':'hi-Deva-IN','target_script':'Devanagari','target_region':'India',
                      'pdf_physical_page':physical or '','printed_page_number':(physical-1 if physical else ''),
                      'pdf_candidate_physical_pages':page_runs(matched or pages),
                      'pdf_page_mapping_status':mapping,'target_context':short(target_cache[path].splitlines()[tline-1]),
                      'rationale':d.get('retrospective_rationale_and_rejected_choices',''),'actual_authorities':str(auth),
                      'authority_verification_status':d['authority_verification_status'],'useful_alternatives':d.get('alternatives_record',''),
                      'confidence':conf,'provisional_status':d.get('status',''),'review_priority':prio,'please_double_check':d['please_double_check'],
                      'open_to_correction':True,'backfill_status':d.get('backfill_status','')}
                    occurrences.append(occurrence)
        else:
            target_locs=d.get('target_locations',[])
            for loc in target_locs or [{}]:
                path=loc.get('path','');ranges=loc.get('complete_original_to_current_changed_ranges',[])
                lines=[]
                for x in ranges:
                    a,b=x.get('after_lines',['','']);lines.append(str(a) if a==b else f'{a}-{b}')
                pages=page_range(path);physical=(pages[0] if len(pages)==1 else '')
                occurrence={'schema_version':SCHEMA_VERSION,'occurrence_id':f"{d['decision_id']}-OCC-{len(occurrences)+1:06d}",'decision_id':d['decision_id'],
                  'kind':d['kind'],'source_term':d.get('chosen_disposition',''),'source_sense_or_domain':d.get('chosen_register',''),
                  'source_unit_id':(bypath[path].get('source_id') or path) if path in bypath else 'shared-config-evidence',
                  'source_path':path if path in bypath else '','source_line':'',
                  'source_line_candidates':f"decision:{d['decision_id']}.source_locations",'source_candidate_count':len(d.get('source_locations',[])),
                  'source_locator_status':'hash_and_changed_range_locator; see source_locations','source_section':'',
                  'target_unit_id':(bypath[path].get('target_id') or path) if path in bypath else 'locale-config',
                  'target_path':path,'target_line':';'.join(lines),'target_hit_in_line':'','target_section':'',
                  'chosen_rendering':d.get('chosen_disposition',''),'target_locale':'hi-Deva-IN','target_script':'Devanagari','target_region':'India',
                  'pdf_physical_page':physical,'printed_page_number':(physical-1 if physical else ''),'pdf_candidate_physical_pages':page_runs(pages),
                  'pdf_page_mapping_status':'file_page_range_from_compiled_entry_counter; correction is not a literal token' if pages else 'shared_config_multi_use; no single printed page',
                  'target_context':'','rationale':d.get('chosen_disposition',''),'actual_authorities':str(auth),'authority_verification_status':d['authority_verification_status'],
                  'useful_alternatives':d.get('alternatives_record',''),'confidence':conf,'provisional_status':'open_to_evidence_based_correction','review_priority':prio,
                  'please_double_check':d['please_double_check'],'open_to_correction':True,'backfill_status':d.get('backfill_status','')}
                occurrences.append(occurrence)
        d['occurrence_count']=sum(1 for x in occurrences if x['decision_id']==d['decision_id'])
        decisions.append(d)
    occurrence_ids={x['occurrence_id'] for x in occurrences};assert len(occurrence_ids)==len(occurrences)
    fields=list(occurrences[0])
    with OUT_CSV.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(occurrences)
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':SCHEMA_VERSION,'title':'OpenLogic translation decision review',
      'description':'Shared core schema implemented first for hi-Deva-IN. Exact and candidate PDF mappings are explicitly distinguished.',
      'type':'object','required':['schema_version','edition','decisions','occurrences','coverage'],
      'properties':{'schema_version':{'const':SCHEMA_VERSION},'edition':{'type':'object'},'decisions':{'type':'array','items':{'type':'object','required':['decision_id','kind','confidence','review_priority','please_double_check']}},
        'occurrences':{'type':'array','items':{'type':'object','required':['occurrence_id','decision_id','target_locale','target_script','target_path','pdf_page_mapping_status']}},'coverage':{'type':'object'}}}
    OUT_SCHEMA.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    exact=sum(bool(x['pdf_physical_page']) for x in occurrences);candidate=sum(not bool(x['pdf_physical_page']) and bool(x['pdf_candidate_physical_pages']) for x in occurrences)
    machine_occurrence_fields=['occurrence_id','decision_id','kind','source_unit_id','source_path','source_line','source_line_candidates','source_candidate_count','source_locator_status','source_section',
      'target_unit_id','target_path','target_line','target_hit_in_line','target_section','pdf_physical_page','printed_page_number','pdf_candidate_physical_pages','pdf_page_mapping_status','target_context']
    machine_occurrences=[{k:x[k] for k in machine_occurrence_fields} for x in occurrences]
    machine={'schema_version':SCHEMA_VERSION,'generated_utc':datetime.now(timezone.utc).isoformat(),
      'edition':{'locale':'hi-Deva-IN','script':'Devanagari','region':'India','source_repository':'OpenLogicProject/OpenLogic','source_commit':SOURCE_COMMIT,
        'reader_pdf':PDF.relative_to(R).as_posix(),'reader_sha256':sha(PDF),'reader_pages':975,'publication_lineage':{'github':'https://github.com/KokunoYumeto/open-logic-hi','zenodo_concept_doi':'10.5281/zenodo.21920511'}},
      'coverage':{'decision_records':len(decisions),'occurrence_rows':len(occurrences),'source_target_graph_paths':722,'terminology_decisions':sum(d['kind']=='terminology' for d in decisions),
        'correction_or_config_decisions':sum(d['kind']!='terminology' for d in decisions),'priority_counts':dict(Counter(d['review_priority'] for d in decisions)),
        'pdf_exact_occurrence_pages':exact,'pdf_candidate_page_rows':candidate,'pdf_unmapped_rows':len(occurrences)-exact-candidate,
        'meaning':'All 400 previously recorded materially judgment-dependent terminology/correction choices are represented. This is not a claim that every ordinary lexical choice in 444k source tokens was independently reconstructed.'},
      'page_mapping_method':{'extraction':'Poppler final reader extraction, 975 form-feed-delimited physical pages','counter_offset':'TeX printed page counter N maps to one-based PDF physical page N+1',
        'exact':'The number/order of exact target-term hits in the file page interval equals the number/order of target TeX literal occurrences.',
        'candidate':'Exact term hits or the compiled file page interval are listed, but not asserted one-to-one. Shared config can have no single page.'},
      'decisions':decisions,'occurrences':machine_occurrences}
    OUT_JSON.write_text(json.dumps(machine,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
    header=['# ओपन लॉजिक परियोजना: हिंदी अनुवाद-निर्णयों की संपूर्ण समीक्षा-सूची','',
      '*Open Logic Project — complete Hindi translation-decision review index*','',
      f'संस्करण: `hi-Deva-IN` (देवनागरी, भारत)। स्थिर स्रोत: `{SOURCE_COMMIT}`। पाठक-संस्करण: 975 पृष्ठ; SHA-256 `{sha(PDF)}`।','',
      f'इस सूची में **{len(decisions)} अभिलिखित सार्थक विवेकाधीन निर्णय** और **{len(occurrences)} लक्ष्य/सुधार उदाहरण** हैं। यह हर साधारण शब्द-चयन के अलग पुनर्निर्माण का दावा नहीं करती। पूर्वव्यापी तर्क को पूर्वव्यापी ही चिह्नित किया गया है। समीक्षा आमंत्रित है, पर प्रकाशन की शर्त नहीं।','',
      'पृष्ठ-संकेत में `p.` मुद्रित संख्या और `PDF` एक-आधारित भौतिक पृष्ठ है। `candidate` पृष्ठ को सटीक नहीं माना गया है। पूरे स्थान और संदर्भ CSV/JSON में हैं।','',
      '| ID | स्रोत पद / अर्थ | हिंदी रूप | लोकैल/लिपि | क्षेत्र | उदाहरण | पृष्ठ | प्राधिकार स्थिति | विकल्प / तर्क | विश्वास | स्थिति | कृपया दोबारा जाँचें |',
      '|---|---|---|---|---|---:|---|---|---|---|---|---|']
    occ_by=defaultdict(list)
    for x in occurrences:occ_by[x['decision_id']].append(x)
    for d in decisions:
        os=occ_by[d['decision_id']];exactpages=sorted({int(x['pdf_physical_page']) for x in os if x['pdf_physical_page']!=''})
        page_label=', '.join(f'p.{x-1}/PDF{x}' for x in exactpages[:12])
        if len(exactpages)>12:page_label+=f' (+{len(exactpages)-12})'
        if not page_label and any(x['pdf_candidate_physical_pages'] for x in os):page_label='candidate; see CSV'
        source=d.get('source_term') or short(d.get('chosen_disposition',''),80)
        chosen=d.get('chosen_target') or short(d.get('chosen_register') or d.get('chosen_disposition',''),90)
        rationale=d.get('retrospective_rationale_and_rejected_choices') or d.get('alternatives_record','')
        header.append('| '+' | '.join(map(md,[d['decision_id'],source,chosen,'hi-Deva-IN / Devanagari',d.get('register_or_domain') or d.get('kind'),len(os),page_label,d['authority_verification_status'],short(rationale,180),d['confidence'],d.get('status') or d['review_priority'],d['please_double_check']]))+' |')
    OUT_FULL.write_text('\n'.join(header)+'\n',encoding='utf-8',newline='\n')
    selected=[d for d in decisions if d['review_priority'] in {'P1','P2'}]
    lines=['# ओपन लॉजिक परियोजना: हिंदी निर्णयों की प्राथमिक समीक्षा','',
      '*Open Logic Project — Hindi priority decision-review view*','',
      f'**{len(decisions)} में से {len(selected)} निर्णय** P1/P2 हैं। P1 में सभी 20 स्पष्टतः अस्थायी पद हैं; P2 में मध्यम-विश्वास या असतत अभिलेख-श्रृंखला वाले मामले हैं। समीक्षा बाद में हो सकती है और पूर्ण पाठक-संस्करण को नहीं रोकती।','',
      '| प्राथमिकता | ID | स्रोत | वर्तमान हिंदी रूप/निर्णय | विश्वास | प्राथमिकता का कारण | कृपया दोबारा जाँचें |','|---|---|---|---|---|---|---|']
    for d in selected:
        why='स्पष्टतः अस्थायी' if d['review_priority']=='P1' else ('ऐतिहासिक हैश-श्रृंखला में अंतर' if d.get('event_chain_gaps') else 'मध्यम विश्वास / साक्ष्य-संवेदी चुनाव')
        lines.append('| '+' | '.join(map(md,[d['review_priority'],d['decision_id'],d.get('source_term') or short(d.get('chosen_disposition',''),90),d.get('chosen_target') or short(d.get('chosen_register') or d.get('chosen_disposition',''),100),d['confidence'],why,d['please_double_check']]))+' |')
    OUT_PRIORITY.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    outputs=[OUT_SCHEMA,OUT_JSON,OUT_CSV,OUT_FULL,OUT_PRIORITY]
    receipt={'schema':SCHEMA_VERSION,'generated_utc':machine['generated_utc'],'status':'PASS_LOCAL_VIEWS_NOT_YET_PUBLISHED','decision_records':len(decisions),'occurrence_rows':len(occurrences),
      'unique_decision_ids':len({d['decision_id'] for d in decisions}),'unique_occurrence_ids':len(occurrence_ids),'priority_counts':machine['coverage']['priority_counts'],
      'pdf_mapping':{'exact_rows':exact,'candidate_rows':candidate,'unmapped_rows':len(occurrences)-exact-candidate},'source_paths':722,'reader_sha256':sha(PDF),
      'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in outputs}}
    OUT_RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
