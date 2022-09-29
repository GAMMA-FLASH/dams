#!/usr/bin/env python3
import h5py
import json
from pathlib import Path
import _pickle as cPickle
import glob,os,bz2
import numpy as np
import datetime,time,csv
from joblib import Parallel, delayed
import argparse

DETECTOR="rpg0"
#directory = "/data/archive/acquisizione_2022_08_15/rpg0/"
directory = "/data/archive/acquisizione_2022_09_05/"+DETECTOR+"/"
#for filename in sorted(glob.iglob(f'{directory}/*-07-29T*.h5')):
#for filename in sorted(glob.iglob(f'{directory}/*08T*.h5')):
#CONVERT(args.File,args.Detector,args.Thershold,args.TFile)
#print(args)
def CONVERT(filename,detector,directory,Threshold=20,TFile='WS_temp.csv'):
 class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NpEncoder, self).default(obj)
 print(TFile)
 infile=open(TFile, mode='r')
 reader=csv.reader(infile) 
 #Tm= {time.mktime(datetime.datetime.strptime(''.join(list(k for k in rows[0] if k.isprintable())), "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timetuple()):rows[1] for rows in reader if rows[1]!=''}
 
 Tm= {rows[0]:rows[1] for rows in reader if rows[0].isnumeric()}

 TempTime=list(map(int,list(Tm.keys())))
  
 TempValue=list(Tm.values())
 TempSI=0
 TempMI=len(Tm)-1
 TAIL=100
 Thr=Threshold
 Sampling=8
 ToT=400
 SamplesOT=ToT/Sampling
 outfile=directory+"/"+detector+"/"+Path(filename).name+detector+"_DST.pbz2"
 print(outfile)
 if (Path(outfile).is_file()):
    return
 PeakList=[]
 print(filename)
 try:
   f=h5py.File(filename, "r")
   Wavef=f['waveforms']
 except:
   print("Error :"+filename)
   return
 for wff in Wavef:
  data={}
  for k in f['waveforms'][wff].attrs.keys():
   data[k]=f['waveforms'][wff].attrs[k]
   try:
    data[k]=data[k].decode("utf-8")
   except (UnicodeDecodeError, AttributeError):
    pass
  Peak={}
  Peak["ATTR"]=json.dumps(data,cls=NpEncoder)
  try:
    ScalF=1000
    wf=f['waveforms'][wff][:,1]
  except:
    ScalF=0.1220852154804
    wf=f['waveforms'][wff][:]
  wf_i=np.where((wf*ScalF)>Thr)
  Peak["WFM"]=wff
  START=0
  END=0
  Peak['Temperature']=0
#  TempSI=0
  for Timi in range(TempSI,TempMI):
    if (abs(TempTime[Timi]-data['tend'])<=abs(TempTime[Timi+1]-data['tend'])):
      Peak['Temperature']=TempValue[Timi]
      TempSI=max(Timi-10,0)
      value = datetime.datetime.utcfromtimestamp(data['tend'])
      break

  for ni in wf_i[0]:
#    for ni in sq:
     if((ni-END)>1):
       if((END-START)>SamplesOT):
          dstart=max(0,START-TAIL)
          dend=min(len(wf)-1,END+TAIL)
          Peak["START"]=START
          Peak["END"]=END
          Peak["MAX"]=max(wf[START:END]*ScalF)
          Peak["INTEGRAL"]=sum(wf[dstart:dend])*ScalF
          Peak["DATA"]=wf[dstart:dend]*ScalF
          PeakList.append(Peak)
       START=ni
       END=ni
     else:
       END=ni
 f.close()
 with bz2.BZ2File(outfile, 'w') as fp: 
    cPickle.dump(PeakList,fp)

if __name__ == "__main__":

  # Initialize parser
  parser = argparse.ArgumentParser()
  
  # Adding optional argument
  parser.add_argument("-f", "--File", help = "File that must be converted", required=True)
  parser.add_argument("-d", "--Detector", help = "Detector" , required=True)
  OD="/data/archive/DL1"
  parser.add_argument("-o", "--Outdir", help = "Output Directory" ,nargs='?',const=OD ,default=OD, required=True)
  parser.add_argument("-th", "--Thershold", help = "Voltage Threshold in mV. Default value 20 mV",nargs='?', const=20, default=20)
  TFile="/data/gammaflash_repos/gammaflash-gui-dash/gui/weather_station/weather_station_temp.txt"
  parser.add_argument("-t", "--TFile", help = "Temperature File" ,nargs='?',const=TFile ,default=TFile)

  # Read arguments from command line
  args = parser.parse_args()

  print(args.TFile)


  CONVERT(args.File,args.Detector,args.Outdir,20,args.TFile)
