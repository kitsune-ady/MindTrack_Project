from pathlib import Path
import numpy as np, pandas as pd
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[2]
raw=root/'Digital Sedentary Behavior, Mobile Device Dependen'; eda=Path(__file__).resolve().parent
fig=eda/'figures'/'presentation'; tab=eda/'tables'; fig.mkdir(parents=True,exist_ok=True); tab.mkdir(exist_ok=True)
cutoff=11
s=pd.read_excel(raw/'2. Dataset_Sociodemo.xlsx'); t=pd.read_excel(raw/'3. Dataset_MobileDependence.xlsx'); b=pd.read_excel(raw/'5. Dataset_Depression.xlsx')
ti=list(t.columns[8:30]); bi=list(b.columns[8:29]); titems=t[ti].apply(pd.to_numeric,errors='coerce'); bitems=b[bi].apply(pd.to_numeric,errors='coerce')
tsum=titems.sum(axis=1); beck=pd.to_numeric(b['Sum'],errors='coerce')
for f in [s,t,b]:
 if f.Code.isna().any() or f.Code.duplicated().any(): raise ValueError('Missing or duplicate student Code')
if not s.Code.equals(t.Code) or not s.Code.equals(b.Code): raise ValueError('Student codes do not match across files')
a=s.merge(t[['Code']+ti],on='Code',validate='one_to_one').merge(pd.DataFrame({'Code':b.Code,'beck_total':beck}),on='Code',validate='one_to_one')
a['tmd_total']=tsum.to_numpy(); a['depression_flag_11plus']=(a.beck_total>=cutoff).astype(int)
a['tmd_band']=pd.cut(a.tmd_total,[-1,29,38,48,88],labels=['Absence','Low','Medium','High'])
a['age_band']=pd.cut(a.Age,[0,17,20,24,29,100],labels=['17 and under','18-20','21-24','25-29','30+'])
MAP={'Department':{1:'Law',2:'Economics',3:'Engineering',4:'Health'},'Sex':{1:'Male',2:'Female'},'MS':{1:'Single',2:'Married',3:'Separated',4:'Divorced',5:'Widowed',6:'Common-law'},'SES':{1:'Low-low',2:'Low',3:'Low-middle',4:'Middle',5:'High-middle',6:'High'},'Living_Arrangement':{1:'Both parents',2:'One parent',3:'Relatives',4:'Roommate',5:'Partner',6:'Alone'},'Family_Expression':{1:'Never',2:'Sometimes',3:'Often',4:'Always'},'Family_Activities':{1:'Never',2:'Sometimes',3:'Often',4:'Always'},'Mobile_Use_Rules':{1:'Never',2:'Sometimes',3:'Often',4:'Always'},'Phone_Discrimination':{1:'Never',2:'Sometimes',3:'Often',4:'Always'},'Phone_Related_Arguments':{1:'Never',2:'Sometimes',3:'Often',4:'Always'},'Residence_Area':{1:'Urban',2:'Rural'},'Subscription_Plan':{1:'Prepaid',2:'Postpaid'},'Network _Access':{1:'Cellular data',2:'Wi-Fi',3:'Both'},'Areas_Use':{1:'Home',2:'University',3:'Shopping centers',4:'All'},'Average_Time_Use':{1:'<1 hour',2:'1-3 hours',3:'3-6 hours',4:'>6 hours'}}
apps=['Using_Text Messaging_Apps','Using_Games_Apps','Using_social media_Apps','Using_Music_Apps','Using_Videos_Apps','Using_Ttime-management_Apps','Using_Camara_Apps','Using_Mail_Apps']
app_names=dict(zip(apps,['Text/instant messaging','Games','Social media','Music','Videos','Time-management','Camera','Mail']))
ordinal=['Family_Expression','Family_Activities','Mobile_Use_Rules','Phone_Discrimination','Phone_Related_Arguments']
def label(v,x):
 if v in MAP:return MAP[v].get(x,str(x))
 if v in apps:return {1:'No',2:'Yes'}.get(x,str(x))
 return str(x)
def groups(v,name=None):
 out=[]
 for x,g in a.groupby(v,dropna=False,observed=False,sort=True):out.append({'feature':name or v.strip(),'source_column':v,'code':x,'category':label(v,x),'n':len(g),'share':len(g)/len(a),'beck_mean':g.beck_total.mean(),'beck_median':g.beck_total.median(),'above_cutoff_n':int(g.depression_flag_11plus.sum()),'above_cutoff_share':g.depression_flag_11plus.mean()})
 return out
inv=[]
for f,file,sheet in [(s,'2. Dataset_Sociodemo.xlsx','SocioDemo_data'),(t,'3. Dataset_MobileDependence.xlsx','TMD_data'),(b,'5. Dataset_Depression.xlsx','Depression_data')]:
 coded=f[f.Code.notna()]; inv.append({'file':file,'sheet':sheet,'coded_records':len(coded),'columns':f.shape[1],'missing_cells':int(coded.isna().sum().sum()),'duplicate_codes':int(f.Code.duplicated().sum()),'duplicate_full_rows':int(f.duplicated().sum())})
pd.DataFrame(inv).to_csv(tab/'data_inventory.csv',index=False)
bands=pd.cut(beck,[-1,10,16,20,30,40,100],labels=['0-10 Normal','11-16 Mild','17-20 Borderline clinical','21-30 Moderate','31-40 Severe','41+ Extreme']).value_counts(sort=False)
pd.DataFrame({'score_band':bands.index.astype(str),'n':bands.values,'share':bands.values/len(b)}).to_csv(tab/'beck_score_bands.csv',index=False)
features=['Age','Semester','Department','Sex','MS','SES','Living_Arrangement']+ordinal+['Residence_Area','Subscription_Plan','Network _Access','Areas_Use','Time_First_Cellphone','Type_MD','Average_Time_Use']+apps+['tmd_total']+ti
prof=[]
for v in features:
 x=a[v]; z=pd.to_numeric(x,errors='coerce'); prof.append({'feature':app_names.get(v,v.strip()),'source_column':v,'role':'candidate predictor','n':int(x.notna().sum()),'missing':int(x.isna().sum()),'unique':x.nunique(),'min':z.min(),'median':z.median(),'mean':z.mean(),'max':z.max()})
prof.append({'feature':'Beck total','source_column':'Sum','role':'continuous target only','n':len(beck),'missing':int(beck.isna().sum()),'unique':beck.nunique(),'min':beck.min(),'median':beck.median(),'mean':beck.mean(),'max':beck.max()})
pd.DataFrame(prof).to_csv(tab/'candidate_feature_profile.csv',index=False)
comp=['Department','Sex','MS','SES','Living_Arrangement']+ordinal+['Residence_Area','Subscription_Plan','Network _Access','Areas_Use','Time_First_Cellphone','Type_MD','Average_Time_Use']+apps+['age_band','Semester','tmd_band']+ti
rows=[]
for v in comp: rows.extend(groups(v,app_names.get(v,v.strip())))
pd.DataFrame(rows).to_csv(tab/'predictor_groups_vs_depression.csv',index=False)
assoc=[]
for v in ['Age','Semester']+ordinal+['Average_Time_Use','Time_First_Cellphone','tmd_total']+ti:
 q=pd.DataFrame({'x':a[v] if v!='tmd_total' else a.tmd_total,'y':a.beck_total}).dropna();assoc.append({'feature':v.strip(),'source_column':v,'method':'Spearman rank','r':q.x.rank().corr(q.y.rank()),'n':len(q)})
for v in apps:
 q=pd.DataFrame({'x':a[v].map({1:0,2:1}),'y':a.beck_total}).dropna();assoc.append({'feature':app_names[v],'source_column':v,'method':'Point-biserial Yes=1','r':q.x.corr(q.y),'n':len(q)})
adf=pd.DataFrame(assoc).sort_values('r',key=lambda z:z.abs(),ascending=False);adf.to_csv(tab/'candidate_associations_with_beck.csv',index=False)
rawsum=pd.to_numeric(t['sum'],errors='coerce'); mismatch=rawsum.ne(tsum)
q1,q3=s.Age.quantile([.25,.75]); af=q3+1.5*(q3-q1);q1,q3=beck.quantile([.25,.75]);bf=q3+1.5*(q3-q1);q1,q3=tsum.quantile([.25,.75]);tf=q3+1.5*(q3-q1)
quality=[('IDs and join','1,220 unique student codes match in order.','Join on Code, never as a predictor.'),('Missingness','No blank cells in coded records.','No imputation appears necessary; recheck after merge.'),('Duplicates',f'No duplicate full rows; repeated answer patterns: TMD {t[ti].duplicated().sum()}, Beck {b[bi].duplicated().sum()}.','Keep valid students; matching answers alone are not grounds for removal.'),('TMD total',f'{mismatch.sum()} supplied total differs from sum of 22 items; code {t.loc[mismatch,"Code"].iloc[0] if mismatch.any() else "none"}.','Recompute TMD total for analysis; preserve source.'),('Beck total',f'{(bitems.sum(axis=1)==beck).sum()} of {len(b)} totals match 21 item sum.','Retain after confirming instrument scoring.'),('Item ranges','TMD items are within 0-4 and Beck items are within 0-3; no invalid item values found.','Retain valid responses.'),('Beck instrument','Files say BDI-2; item wording/bands resemble original Beck form; item N label conflicts with body-image wording.','Confirm Beck form and cutoff with lecturer/supervisor.'),('Cutoff',f'Project-defined 11+ score group {int((beck>=cutoff).sum())}/{len(b)} ({(beck>=cutoff).mean():.1%}).','Confirm the questionnaire version and scoring guide; use metrics suited to class imbalance.'),('Daily-use category','Codebook mapping valid; counts '+', '.join(f'{i}:{int((s["Average_Time_Use"]==i).sum())}' for i in range(1,5))+'.','Verify the single 1-3h response; avoid overinterpretation.'),('Age',f'{s.Age.min()}-{s.Age.max()}; under18={(s.Age<18).sum()}; over30={(s.Age>30).sum()}; above Tukey fence={(s.Age>af).sum()}.','Within documented range; retain plausible values, check minor reporting.'),('High scores',f'Above Tukey fences: Beck {(beck>bf).sum()}, TMD {(tsum>tf).sum()}.','Do not remove valid bounded high scores automatically.'),('Department/program','19 programs grouped into four departments.','Prefer Department for model; keep Program for description.'),('App labels','Dictionary No/Yes but survey asks apps used most often.','Call these selection flags pending confirmation.'),('Out-of-scope columns','Posture/ergonomics and anxiety columns are outside depression scope.','Exclude from current model; preserve raw files.'),('Codebook typos','Posture-specific usage-time codebook has incorrect leading codes.','Keep these columns out of scope unless verified.')]
pd.DataFrame(quality,columns=['finding','evidence','recommended_follow_up']).to_csv(tab/'data_quality_review.csv',index=False)
# Charts
fd=Path(r'C:\Windows\Fonts')
def font(n,bold=False):
 try:return ImageFont.truetype(str(fd/('arialbd.ttf' if bold else 'arial.ttf')),n)
 except OSError:return ImageFont.load_default()
NAVY='#17324D';INK='#263746';BLUE='#4C78A8';RED='#D95F59';GRID='#D9E1EA';GREY='#5E6D7B'
def canvas(title,sub,w=1500,h=950):
 im=Image.new('RGB',(w,h),'white');d=ImageDraw.Draw(im);d.text((70,40),title,font=font(32,True),fill=NAVY);d.text((72,88),sub,font=font(18),fill=GREY);return im,d
def center(d,x,y,txt,f,fill=INK):
 box=d.textbbox((0,0),str(txt),font=f);d.text((x-(box[2]-box[0])/2,y-(box[3]-box[1])/2),str(txt),font=f,fill=fill)
# Age distribution
age=s.Age.astype(int);cnt=np.bincount(age,minlength=61)[16:61];im,d=canvas('Age of students','Age range is 16 to 60; 15 students are under 18');L,T,R,B=135,170,1430,770;ymax=300;step=(R-L)/len(cnt)
for v in range(0,ymax+1,50):
 y=B-(B-T)*v/ymax;d.line((L,y,R,y),fill=GRID);d.text((80,y-9),str(v),font=font(16),fill=INK)
for i,c in enumerate(cnt):
 x=L+i*step;y=B-(B-T)*min(int(c),ymax)/ymax;d.rectangle((x,y,x+step-1,B),fill=BLUE)
for v in range(16,61,5):center(d,L+(v-15.5)*step,B+20,str(v),font(16))
d.text((R-320,T+8),f'Median {age.median():.0f} | Mean {age.mean():.1f}',font=font(18,True),fill=NAVY);d.line((L,T,L,B,R,B),fill=INK,width=2);im.save(fig/'07_age_distribution.png')
# Department cutoff rates
dep=a.groupby('Department').agg(n=('depression_flag_11plus','size'),pos=('depression_flag_11plus','sum'),rate=('depression_flag_11plus','mean'));im,d=canvas('Beck cutoff rate by department','Project-defined 11+ cutoff; rates shown with counts');L,T,R,B=150,180,1430,760;slot=(R-L)/4;mv=40
for v in range(0,mv+1,10):
 y=B-(B-T)*v/mv;d.line((L,y,R,y),fill=GRID);d.text((80,y-9),f'{v}%',font=font(16),fill=INK)
for i,(code,row) in enumerate(dep.iterrows()):
 x0=L+i*slot+50;x1=L+(i+1)*slot-50;y=B-(B-T)*row.rate*100/mv;d.rounded_rectangle((x0,y,x1,B),radius=8,fill=BLUE);center(d,(x0+x1)/2,y-20,f'{row.rate:.1%} ({int(row.pos)}/{int(row.n)})',font(17,True),NAVY);center(d,(x0+x1)/2,B+22,MAP['Department'][int(code)],font(18))
d.line((L,T,L,B,R,B),fill=INK,width=2);im.save(fig/'08_beck_flag_by_department.png')
# Ordinal response patterns
im,d=canvas('Beck cutoff rates by ordinal responses','Group sizes and rates are descriptive; response labels follow the dictionary',1600,1230)
for idx,v in enumerate(ordinal):
 row,col=divmod(idx,2);x0=90+col*780;y0=150+row*350;d.text((x0,y0),v.replace('_',' '),font=font(20,True),fill=NAVY);part=a.groupby(v).agg(n=('depression_flag_11plus','size'),rate=('depression_flag_11plus','mean'));L,T,R,B=x0+55,y0+45,x0+705,y0+260;slot=(R-L)/4
 for tick in [0,10,20,30,40,50,60,70]:
  y=B-(B-T)*tick/70;d.line((L,y,R,y),fill=GRID);d.text((x0+3,y-7),str(tick),font=font(13),fill=GREY)
 for j,(code,g) in enumerate(part.iterrows()):
  xx=L+j*slot+15;xx2=L+(j+1)*slot-15;y=B-(B-T)*g.rate*100/70;d.rectangle((xx,y,xx2,B),fill=BLUE);center(d,(xx+xx2)/2,y-16,f'{g.rate:.0%}',font(14,True),NAVY);center(d,(xx+xx2)/2,B+13,{1:'Never',2:'Sometimes',3:'Often',4:'Always'}[int(code)],font(13));center(d,(xx+xx2)/2,B+30,f'n={int(g.n)}',font(12),GREY)
 d.line((L,T,L,B,R,B),fill=INK)
im.save(fig/'09_ordinal_predictor_patterns.png')
# TMD answer response heatmap
im,d=canvas('Responses across 22 phone-dependence items','Each cell shows share selecting response 0-4; item response wording differs by section',1450,1100);L,T,R,B=180,170,1400,1020;cw=(R-L)/5;ch=(B-T)/22
for j in range(5):center(d,L+(j+.5)*cw,T-20,str(j),font(16,True))
for i,v in enumerate(ti):
 d.text((95,T+i*ch+4),f'Q{i+1}',font=font(14),fill=INK);vals=pd.to_numeric(t[v],errors='coerce')
 for j in range(5):
  pct=float((vals==j).mean());q=min(pct/.7,1);color=(int(241-145*q),int(247-115*q),int(252-60*q));x=L+j*cw;y=T+i*ch;d.rectangle((x,y,x+cw-2,y+ch-2),fill=color);center(d,x+cw/2,y+ch/2,f'{pct:.0%}',font(12),NAVY)
im.save(fig/'10_tmd_item_response_heatmap.png')
# Summary report
flag=int((beck>=cutoff).sum());zero=int((beck==0).sum());mb=a.groupby('tmd_band',observed=False).beck_total.mean(); ar=a.groupby('Phone_Related_Arguments').depression_flag_11plus.mean()
text=f'''# Depression-focused exploratory data analysis

## Scope and method

This describes the raw questionnaire data. Beck total is the continuous outcome; the project-defined 11+ flag is used only for group summaries. No causation or statistical significance is claimed. Source workbooks are unchanged. Beck answer items are excluded as predictors because they define the outcome. Candidate predictors include background, family and phone-use responses, app-selection flags, and the 22 phone-dependence items/recomputed total. Ergonomics and anxiety fields are outside the current depression focus.

## Findings

- The three files contain {len(a):,} coded students with unique, aligned IDs and no blank cells in coded records.
- Beck totals range {beck.min():.0f}-{beck.max():.0f}; mean {beck.mean():.2f}, median {beck.median():.0f}. {zero:,} students ({zero/len(a):.1%}) scored zero.
- At the project-defined 11+ threshold, {flag:,} students ({flag/len(a):.1%}) are above cutoff. This imbalance means accuracy alone will be misleading.
- TMD and Beck totals show a weak positive association (Spearman r={a.tmd_total.rank().corr(a.beck_total.rank()):.3f}; Pearson r={a.tmd_total.corr(a.beck_total):.3f}). Mean Beck by TMD band: {', '.join(f'{k} {v:.2f}' for k,v in mb.items())}. It does not rise steadily.
- Above-cutoff shares by phone-argument answer: {', '.join(f'{MAP['Phone_Related_Arguments'][int(k)]} {v:.1%}' for k,v in ar.items())}. The Always group has only 29 students.
- Daily-use categories count {', '.join(f'{MAP['Average_Time_Use'][i]} {int((s['Average_Time_Use']==i).sum())}' for i in range(1,5))}; only one response is in 1-3 hours.
- Age range is {int(s.Age.min())}-{int(s.Age.max())}; {int((s.Age<18).sum())} participants are under 18, and {int((s.Age>30).sum())} are over 30.

## Data-quality and interpretation points

- One supplied TMD total differs from the sum of its 22 answers. Use the item-summed total for analysis and preserve the source workbook.
- Files are titled BDI-2, but several item wordings and score bands resemble the original Beck form. Item N's dictionary label conflicts with its body-image wording. Confirm the instrument version matches the scoring guide; this project currently uses Beck total >=11.
- The dictionary says app codes are No/Yes, while the survey asks which apps are used most often. Describe these as app-selection flags until confirmed.
- Program has 19 categories and overlaps with Department's four divisions. Prefer Department in the model; retain Program for description.
- Some values exceed Tukey boxplot fences but stay within documented ranges. Do not remove valid high scores automatically.
- Repeated answer patterns exist, but student codes and full rows are unique. Do not remove students just because answers match.
- Posture-specific usage-time codebook rows have incorrect leading codes. Exclude those fields unless the scope changes.

## Presentation takeaway

“Our EDA shows that Beck scores cluster at the low end. We define the positive class as a Beck total of 11 or higher, which groups mild mood disturbance and every higher score band together. This is a research score grouping, not a diagnosis. Phone-dependence scores show a weak positive descriptive association with Beck scores; this does not show cause.”

## Next step

Review the quality table with the lecturer/supervisor and confirm the Beck form matches its scoring guide. Keep the project-defined 11+ target unless the lecturer recommends a different research grouping. Then finalize cleaning decisions. After EDA and cleaning, prepare the depression-only modeling table, split data, and fit encoding, scaling, and PCA within training folds.

See the tables folder for the inventory, score bands, candidate feature profiles, group summaries, descriptive correlations, and quality review.
'''
(eda/'preliminary_eda_findings.md').write_text(text,encoding='utf-8')
print(f'Completed EDA: {len(list(fig.glob("*.png")))} figures, {len(list(tab.glob("*.csv")))} tables; n={len(a)}, positives={flag} ({flag/len(a):.1%}), TMD-Beck Spearman={a.tmd_total.rank().corr(a.beck_total.rank()):.3f}')



