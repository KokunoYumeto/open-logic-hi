"""One-pass deterministic validation of the Hindi decision-review surfaces."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv, hashlib, json, unicodedata

R=Path(__file__).resolve().parents[1]
TERM=R/'04_terminology'
Q=R/'07_qa/openlogic/HI-OLP-READER-RECONCILED-20260904'
S=R/'02_source_snapshot/openlogic_en_9620cc7/content'
T=R/'05_translation/openlogic_hi_9620cc7/locale/hi/content'
OUT=TERM/'DECISION_REVIEW_VALIDATION.json'
CONFIG_PATH='05_translation/openlogic_hi_9620cc7/locale/hi/open-logic-config.sty'
CONFIG_FILE=T.parent/'open-logic-config.sty'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def check(name, condition, detail):
    if not condition: raise AssertionError(f'{name}: {detail}')
    return {'check':name,'status':'PASS','detail':detail}

def main():
    ledger_path=TERM/'SUBSTANTIVE_DECISION_LOG.jsonl'
    machine_path=TERM/'DECISION_REVIEW_MACHINE.json'
    csv_path=TERM/'DECISION_OCCURRENCES.csv'
    full_path=TERM/'DECISION_REVIEW_INDEX.md'
    priority_path=TERM/'DECISION_REVIEW_PRIORITY.md'
    schema_path=TERM/'DECISION_REVIEW_SCHEMA.json'
    build_receipt_path=TERM/'DECISION_REVIEW_RECEIPT.json'
    ledger=[json.loads(x) for x in ledger_path.read_text(encoding='utf-8').splitlines() if x.strip()]
    machine=json.loads(machine_path.read_text(encoding='utf-8'))
    schema=json.loads(schema_path.read_text(encoding='utf-8'))
    build_receipt=json.loads(build_receipt_path.read_text(encoding='utf-8'))
    graph=json.loads((Q/'INTEGRATED_READER_EVIDENCE.json').read_text(encoding='utf-8'))['records']
    graph_paths={x['path'] for x in graph}
    decisions=machine['decisions']; occurrences=machine['occurrences']
    ledger_by={x['decision_id']:x for x in ledger}; decision_by={x['decision_id']:x for x in decisions}
    results=[]
    results.append(check('decision_count',len(ledger)==len(decisions)==400,'400 ledger and machine decisions'))
    results.append(check('decision_ids',set(ledger_by)==set(decision_by),'machine IDs equal ledger IDs'))
    stable_fields=('kind','source_term','chosen_target','chosen_disposition','chosen_register')
    drift=[]
    for did,src in ledger_by.items():
        dst=decision_by[did]
        for field in stable_fields:
            if src.get(field)!=dst.get(field): drift.append(f'{did}:{field}')
    results.append(check('decision_meaning_fields',not drift,'kind/source/chosen fields unchanged'))
    term_expected=sum(int(x.get('target_literal_hits',0)) for x in ledger if x['kind']=='terminology')
    other_expected=sum(len(x.get('target_locations',[]) or [{}]) for x in ledger if x['kind']!='terminology')
    expected=term_expected+other_expected
    results.append(check('occurrence_count',len(occurrences)==expected,f'{term_expected} literal + {other_expected} correction/config = {expected}'))
    occ_ids=[x['occurrence_id'] for x in occurrences]
    results.append(check('occurrence_ids',len(set(occ_ids))==len(occ_ids),'all occurrence IDs unique'))
    results.append(check('referential_integrity',all(x['decision_id'] in decision_by for x in occurrences),'every occurrence resolves to one decision'))
    actual_counts=Counter(x['decision_id'] for x in occurrences)
    expected_counts={x['decision_id']:(int(x.get('target_literal_hits',0)) if x['kind']=='terminology' else len(x.get('target_locations',[]) or [{}])) for x in ledger}
    results.append(check('per_decision_counts',actual_counts==Counter(expected_counts),'each decision occurrence count reconciles'))
    bad_target=[x['occurrence_id'] for x in occurrences if x['target_path'] not in graph_paths|{'open-logic-config.sty',CONFIG_PATH}]
    bad_source=[x['occurrence_id'] for x in occurrences if x.get('source_path') and x['source_path'] not in graph_paths]
    results.append(check('accepted_graph_paths',not bad_target and not bad_source,'all non-config source/target locators are in 722-file graph'))
    source_line_counts={p:len((S/p).read_text(encoding='utf-8-sig').splitlines()) for p in {x.get('source_path') for x in occurrences if x.get('source_path')}}
    target_line_counts={p:len((T/p).read_text(encoding='utf-8-sig').splitlines()) for p in {x['target_path'] for x in occurrences if x['target_path'] in graph_paths}}
    target_line_counts['open-logic-config.sty']=len(CONFIG_FILE.read_text(encoding='utf-8-sig').splitlines())
    line_errors=[]
    for x in occurrences:
        if x.get('source_line') and not 1<=int(x['source_line'])<=source_line_counts[x['source_path']]: line_errors.append(x['occurrence_id']+':source')
        if x['kind']=='target_literal_occurrence' and not 1<=int(x['target_line'])<=target_line_counts[x['target_path']]: line_errors.append(x['occurrence_id']+':target')
    results.append(check('line_bounds',not line_errors,'all selected exact source and target lines exist'))
    page_errors=[]
    for x in occurrences:
        if x.get('pdf_physical_page')!='':
            p=int(x['pdf_physical_page'])
            if not 1<=p<=975 or int(x['printed_page_number'])!=p-1: page_errors.append(x['occurrence_id'])
    results.append(check('page_bounds',not page_errors,'every exact physical page is 1..975 and printed page is physical-1'))
    csv_ids=[]; csv_pairs=[]
    with csv_path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        required={'occurrence_id','decision_id','source_term','source_path','source_line','target_path','target_line','pdf_page_mapping_status','please_double_check'}
        results.append(check('csv_columns',required<=set(reader.fieldnames or []),'review and locator columns present'))
        for row in reader:
            csv_ids.append(row['occurrence_id']); csv_pairs.append((row['occurrence_id'],row['decision_id']))
    machine_pairs=[(x['occurrence_id'],x['decision_id']) for x in occurrences]
    results.append(check('csv_rows',len(csv_ids)==expected,f'{expected} parsed data rows'))
    results.append(check('csv_machine_order',csv_pairs==machine_pairs,'CSV occurrence/decision sequence equals machine JSON'))
    full=full_path.read_text(encoding='utf-8'); priority=priority_path.read_text(encoding='utf-8')
    results.append(check('full_index_ids',all(full.count(f'| {did} |')==1 for did in decision_by),'each decision appears once in full index'))
    expected_priority={d['decision_id'] for d in decisions if d['review_priority'] in {'P1','P2'}}
    results.append(check('priority_index_ids',all(priority.count(f'| {decision_by[did]["review_priority"]} | {did} |')==1 for did in expected_priority) and all(did not in priority for did in set(decision_by)-expected_priority),f'{len(expected_priority)} P1/P2 IDs and no P3 IDs'))
    required_top=set(schema['required'])
    results.append(check('schema_required',required_top<=set(machine),'machine object satisfies declared top-level required keys'))
    text_paths=[machine_path,csv_path,full_path,priority_path,schema_path,build_receipt_path]
    unicode_bad=[]
    for path in text_paths:
        text=path.read_text(encoding='utf-8-sig')
        if text.encode('utf-8').decode('utf-8')!=text: unicode_bad.append(path.name)
    results.append(check('utf8_roundtrip',not unicode_bad,'all six review surfaces decode and round-trip as UTF-8'))
    deva=sum(any('\u0900'<=c<='\u097f' for c in d.get('chosen_target','')) for d in decisions if d['kind']=='terminology')
    results.append(check('locale_metadata',machine['edition']['locale']=='hi-Deva-IN' and machine['edition']['script']=='Devanagari',f'hi-Deva-IN / Devanagari; {deva}/357 terminology renderings contain Devanagari'))
    output_hashes={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [schema_path,machine_path,csv_path,full_path,priority_path,build_receipt_path]}
    for name,meta in build_receipt['outputs'].items():
        results.append(check('builder_hash_'+name,output_hashes[name]['bytes']==meta['bytes'] and output_hashes[name]['sha256']==meta['sha256'],'builder receipt matches current bytes'))
    receipt={'schema':'openlogic-translation-decision-review-validation/1.0.0','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS',
      'checks':results,'counts':{'decisions':len(decisions),'occurrences':len(occurrences),'literal_occurrences':term_expected,'correction_or_config_occurrences':other_expected,'priority_decisions':len(expected_priority)},
      'inputs':{'ledger':{'path':ledger_path.relative_to(R).as_posix(),'bytes':ledger_path.stat().st_size,'sha256':sha(ledger_path)},'accepted_graph':{'path':(Q/'INTEGRATED_READER_EVIDENCE.json').relative_to(R).as_posix(),'bytes':(Q/'INTEGRATED_READER_EVIDENCE.json').stat().st_size,'sha256':sha(Q/'INTEGRATED_READER_EVIDENCE.json')}},
      'outputs':output_hashes,'limitations':['Source/target pairing marked inferred is a deterministic nearest-line locator, not a semantic-alignment claim.','Candidate PDF page ranges are not represented as exact pages.','The retrospective ledger covers 400 materially judgment-dependent choices; it is not an exhaustive token-by-token lexicon.']}
    OUT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':'PASS','checks':len(results),'decisions':len(decisions),'occurrences':len(occurrences),'output':str(OUT),'sha256':sha(OUT)},indent=2))

if __name__=='__main__': main()
