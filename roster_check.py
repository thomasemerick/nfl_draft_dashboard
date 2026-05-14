import nflreadpy as nfl
import pandas as pd

# F-S chart
fs_chart = {
    1:3000,2:2649,3:2443,4:2297,5:2184,6:2092,7:2014,8:1946,
    9:1887,10:1833,11:1785,12:1741,13:1700,14:1663,15:1628,16:1595,
    17:1564,18:1535,19:1508,20:1482,21:1457,22:1434,23:1411,24:1389,
    25:1369,26:1349,27:1330,28:1311,29:1294,30:1276,31:1260,32:1244,
    33:1228,34:1213,35:1198,36:1184,37:1170,38:1157,39:1143,40:1131,
    41:1118,42:1106,43:1094,44:1082,45:1071,46:1060,47:1049,48:1039,
    49:1028,50:1018,51:1008,52:999,53:989,54:980,55:971,56:962,
    57:953,58:944,59:936,60:927,61:919,62:911,63:903,64:895,
    65:888,66:880,67:873,68:865,69:858,70:851,71:844,72:837,
    73:831,74:824,75:817,76:811,77:805,78:798,79:792,80:786,
    81:780,82:774,83:768,84:762,85:757,86:751,87:745,88:740,
    89:735,90:729,91:724,92:719,93:713,94:708,95:703,96:698,
    97:694,98:689,99:684,100:679,101:675,102:670,103:665,104:661,
    105:656,106:652,107:647,108:643,109:639,110:634,111:630,112:626,
    113:622,114:617,115:613,116:609,117:605,118:601,119:597,120:594,
    121:590,122:586,123:582,124:579,125:575,126:571,127:568,128:564,
    129:561,130:557,131:554,132:550,133:547,134:543,135:540,136:537,
    137:533,138:530,139:527,140:524,141:520,142:517,143:514,144:511,
    145:508,146:505,147:502,148:499,149:496,150:493,151:490,152:487,
    153:484,154:482,155:479,156:476,157:473,158:471,159:468,160:465,
    161:463,162:460,163:458,164:455,165:453,166:450,167:448,168:445,
    169:443,170:441,171:438,172:436,173:434,174:431,175:429,176:427,
    177:425,178:422,179:420,180:418,181:416,182:414,183:412,184:410,
    185:407,186:405,187:403,188:401,189:399,190:397,191:395,192:393,
    193:392,194:390,195:388,196:386,197:384,198:382,199:381,200:379,
    201:377,202:375,203:374,204:372,205:370,206:368,207:367,208:365,
    209:363,210:362,211:360,212:358,213:357,214:355,215:353,216:352,
    217:350,218:349,219:347,220:345,221:344,222:342,223:341,224:339,
    225:338,226:336,227:335,228:333,229:332,230:330,231:329,232:327,
    233:326,234:325,235:323,236:322,237:320,238:319,239:317,240:316,
    241:315,242:313,243:312,244:310,245:309,246:308,247:306,248:305,
    249:303,250:302,251:301,252:299,253:298,254:297,255:295,256:294,
    257:293
}

# Load current rosters
rosters = nfl.load_rosters().to_pandas()
rosters["full_name"] = rosters["full_name"].str.strip()

# Pull 2021 draft picks from nflverse
url = "https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv"
draft_all = pd.read_csv(url)
draft_2021 = draft_all[draft_all["season"] == 2021].copy()
draft_2021["pfr_player_name"] = draft_2021["pfr_player_name"].str.strip()

# Add F-S value per pick slot
draft_2021["fs_value"] = draft_2021["pick"].map(fs_chart)

# Match on gsis_id
merged = draft_2021.merge(
    rosters[["full_name","team","status","years_exp","gsis_id"]],
    on="gsis_id",
    how="left"
)

merged["on_roster"] = merged["team_y"].notna()

# ROI = w_av / fs_value per player
merged["av_per_fs"] = (merged["w_av"] / merged["fs_value"]).round(4)

# Team summary
hit_rate = merged.groupby("team_x").agg(
    total_picks=("pfr_player_name","count"),
    on_roster=("on_roster","sum"),
    total_fs_value=("fs_value","sum"),
    total_w_av=("w_av","sum"),
    avg_seasons_started=("seasons_started","mean"),
    avg_w_av=("w_av","mean"),
    avg_av_per_fs=("av_per_fs","mean")
).reset_index()

hit_rate["hit_rate"] = (hit_rate["on_roster"] / hit_rate["total_picks"] * 100).round(1)
hit_rate["avg_av_per_fs"] = (hit_rate["avg_av_per_fs"] * 1000).round(1)
hit_rate["total_w_av"] = hit_rate["total_w_av"].round(1)
hit_rate["total_fs_value"] = hit_rate["total_fs_value"].round(0).astype(int)
hit_rate["avg_seasons_started"] = hit_rate["avg_seasons_started"].round(1)
hit_rate["avg_av_per_fs"] = hit_rate["avg_av_per_fs"].round(4)
hit_rate = hit_rate.sort_values("avg_av_per_fs", ascending=False)

print(hit_rate.rename(columns={"team_x":"team"}).to_string(index=False))

# Denver Broncos 2021 draft class breakdown
den = merged[merged["team_x"] == "DEN"][
    ["pfr_player_name","round","pick","position","college",
     "seasons_started","w_av","fs_value","av_per_fs","on_roster"]
].sort_values("pick")

den["on_roster"] = den["on_roster"].map({True:"Yes", False:"No"})
den["w_av"] = den["w_av"].fillna(0).astype(int)
den["seasons_started"] = den["seasons_started"].fillna(0).astype(int)

print("\nDenver Broncos 2021 Draft Class:")
print(den.to_string(index=False))