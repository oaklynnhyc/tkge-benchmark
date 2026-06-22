#!/usr/bin/env python3
"""FinReflect -> TIMEPLEX(tkbi) 區間輸入（走 use_time_interval / 別名 WIKIDATA12k），零改碼。
tkbi 讀 l[0]=subject l[1]=relation l[2]=object l[3:5]=(start,end)（字串名稱，map 由 tkbi 自建）；
非 icews 名稱→以 '-' 切 4 位年；跑時加 --flag_bin 觸發 use_time_interval、--filter_method time-interval。
真實 start/end 還原政策同 to_hyte_interval。輸出 data_ready/timeplex_interval/WIKIDATA12k/{train,valid,test}.txt
"""
import csv, json, re, pathlib
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parents[1]; DS="finreflect"
YEAR_RE=re.compile(r"(19|20)\d{2}")
def parse_year(s,fb):
    m=YEAR_RE.search(s or ""); return m.group(0) if m else fb
def build_interval_map():
    agg={}
    with open(ROOT/"data_source"/DS/"finreflect_sample2000.tsv") as f:
        for r in csv.DictReader(f,delimiter="\t"):
            yr=r["year"].strip(); key=(r["entity"].strip(),r["relationship"].strip(),r["target"].strip(),yr)
            sy=parse_year(r.get("start_date",""),yr); ey=parse_year(r.get("end_date",""),yr)
            if int(ey)<int(sy): ey=sy
            agg[key]=(min(agg[key][0],sy),max(agg[key][1],ey)) if key in agg else (sy,ey)
    return agg
def main():
    imap=build_interval_map()
    dst=ROOT/"data_ready"/"timeplex_interval"/"WIKIDATA12k"; dst.mkdir(parents=True,exist_ok=True)
    n={}; real=0
    for sp in ("train","valid","test"):
        rows=[]
        with open(ROOT/"data_source"/DS/f"{sp}.tsv") as f:
            for r in csv.DictReader(f,delimiter="\t"):
                s,rel,o,y=r["subject"].strip(),r["relation"].strip(),r["object"].strip(),r["year"].strip()
                a,b=imap.get((s,rel,o,y),(y,y)); real+=(a!=b)
                rows.append(f"{s}\t{rel}\t{o}\t{a}-##-##\t{b}-##-##")
        open(dst/f"{sp}.txt","w").write("\n".join(rows)+"\n"); n[sp]=len(rows)
    json.dump({"variant":"interval","alias":"WIKIDATA12k","rows_real_interval":real,"splits":n},
              open(dst/"map_meta.json","w"),ensure_ascii=False,indent=2)
    print("TIMEPLEX-interval ->",dst); print(n,"real_interval_rows=",real)
if __name__=="__main__": main()
