#!/usr/bin/env python3
"""FinReflect -> TeRo(ATISE repo) 區間輸入（走 Dataset_YG / data_dir='yago'），零改碼。
TeRo 的 YAGO 路徑 (Dataset_YG) 讀 5 欄：head_id  rel_id  tail_id  START-##-##  END-##-##
（以 '-' 切出 4 位年；year2id 依 count 門檻分箱；rank 在 --timedisc 1 下用對偶關係配 start/end）。
真實 start/end 由原始 finreflect_sample2000.tsv 還原（同 to_hyte_interval 的政策：
default/無法解析→回退 year 欄；end<start→收成點；同 quad 取 min(start)/max(end)）。
輸出：data_ready/tero_interval/finreflect/yago/{entity2id,relation2id,train,valid,test}.txt
"""
import csv, json, re, pathlib
from collections import defaultdict
ROOT = pathlib.Path(__file__).resolve().parents[1]; DS="finreflect"
YEAR_RE = re.compile(r"(19|20)\d{2}")
def parse_year(s, fb):
    m=YEAR_RE.search(s or ""); return m.group(0) if m else fb
def build_interval_map():
    agg={}; st=defaultdict(int)
    with open(ROOT/"data_source"/DS/"finreflect_sample2000.tsv") as f:
        for r in csv.DictReader(f,delimiter="\t"):
            yr=r["year"].strip()
            key=(r["entity"].strip(),r["relationship"].strip(),r["target"].strip(),yr)
            sy=parse_year(r.get("start_date",""),yr); ey=parse_year(r.get("end_date",""),yr)
            if int(ey)<int(sy): ey=sy; st["reversed_collapsed"]+=1
            agg[key]=(min(agg[key][0],sy),max(agg[key][1],ey)) if key in agg else (sy,ey)
    return agg,st
def read_split():
    out={}
    for sp in ("train","valid","test"):
        rows=[]
        with open(ROOT/"data_source"/DS/f"{sp}.tsv") as f:
            for r in csv.DictReader(f,delimiter="\t"):
                rows.append((r["subject"].strip(),r["relation"].strip(),r["object"].strip(),r["year"].strip()))
        out[sp]=rows
    return out
def main():
    imap,st=build_interval_map(); data=read_split()
    allrows=[q for p in data.values() for q in p]
    def iv(s,r,o,y): return imap.get((s,r,o,y),(y,y))
    ents=sorted({q[0] for q in allrows}|{q[2] for q in allrows}); rels=sorted({q[1] for q in allrows})
    eid={e:i for i,e in enumerate(ents)}; rid={r:i for i,r in enumerate(rels)}
    dst=ROOT/"data_ready"/"tero_interval"/DS/"yago"; dst.mkdir(parents=True,exist_ok=True)
    open(dst/"entity2id.txt","w").write("".join(f"{e}\t{i}\n" for e,i in eid.items()))
    open(dst/"relation2id.txt","w").write("".join(f"{r}\t{i}\n" for r,i in rid.items()))
    real=0
    for sp,rows in data.items():
        with open(dst/f"{sp}.txt","w") as f:
            for s,r,o,y in rows:
                a,b=iv(s,r,o,y); real+= (a!=b)
                f.write(f"{eid[s]}\t{rid[r]}\t{eid[o]}\t{a}-##-##\t{b}-##-##\n")
    json.dump({"variant":"interval","dataset":DS,"n_entity":len(ents),"n_relation":len(rels),
               "rows_real_interval(start!=end)":real,"policy":dict(st),
               "splits":{k:len(v) for k,v in data.items()}},
              open(dst/"time_map.json","w"),ensure_ascii=False,indent=2)
    print("TeRo-interval ->",dst); print(json.load(open(dst/"time_map.json")))
if __name__=="__main__": main()
