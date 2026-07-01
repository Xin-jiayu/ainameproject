# 鎴愬憳 C 浜ゆ帴鏂囨。

## 1. 褰撳墠鑱岃矗鑼冨洿

鎴愬憳 C 璐熻矗 AI 宸ヤ綔娴併€丷AG 鐭ヨ瘑搴撴帴鍏ャ€丳rompt 璐ㄩ噺浼樺寲銆佽捣鍚嶅垎绫昏矾鐢便€佸弽棣堣蹇嗛摼璺拰鍩虹鏍￠獙閫昏緫銆?

涓嶅綊鎴愬憳 C 涓昏矗鐨勫唴瀹癸細

- 鐢ㄦ埛琛ㄣ€侀搴﹀瓧娈点€佷笟鍔¤褰曡〃绛夋暟鎹簱缁撴瀯
- Alembic 杩佺Щ缁存姢
- 鐧诲綍娉ㄥ唽銆丣WT 閴存潈銆佸厤璐规鏁版墸鍑?
- 鍓嶇椤甸潰甯冨眬鍜屼氦浜掍綋楠?

杩欎簺鍐呭鍒嗗埆鐢辨垚鍛?A 鍚庣/鏁版嵁搴撱€佹垚鍛?B 鍓嶇缁х画缁存姢銆?

## 2. 鏈疆瀹屾垚鍐呭

### 2.1 涓夌被璧峰悕璺敱纭

鏂囦欢锛?

- `ainame/core/workflow.py`

褰撳墠璺敱鍏崇郴锛?

```text
浜哄悕   -> human_naming_node
浼佷笟鍚?-> company_naming_node
瀹犵墿鍚?-> pet_naming_node
```

宸插鐞嗙偣锛?

- 宸ヤ綔娴佽妭鐐瑰悕绉板拰璺敱杩斿洖鍊煎凡缁忓榻愩€?
- 鏈煡 `category` 浼氭姏鍑烘槑纭敊璇紝涓嶅啀闈欓粯澶辫触銆?
- 鍘熷厛缁撴潫杈归噷浼佷笟鑺傜偣鏈纭粨鏉熺殑闂宸茬粡淇銆?

鏈煡鍒嗙被閿欒绀轰緥锛?

```text
鏈煡璧峰悕鍒嗙被: '娓告垙瑙掕壊'锛屽厑璁稿€? 浜哄悕銆佷紒涓氬悕銆佸疇鐗╁悕
```

### 2.2 thread_id 璁板繂閫昏緫纭

鏂囦欢锛?

- `ainame/core/workflow.py`
- `ainame/routers/name_router.py`

褰撳墠瑙勫垯锛?

- `/names/generate` 棣栨鐢熸垚鏃跺垱寤烘柊鐨?`thread_id`
- `thread_id` 浼氫紶鍏?LangGraph config锛?

```python
{"configurable": {"thread_id": thread_id}}
```

- `/names/feedback` 澶嶇敤鍓嶇浼犳潵鐨勬棫 `thread_id`
- 鍙嶉鎺ュ彛浼氬厛鎸?`thread_id` 鏌ュ巻鍙茶褰曪紝鏌ヤ笉鍒板垯杩斿洖 404
- 鍙嶉涓嶄細鏂板缓 `thread_id`

鎴愬憳 B 鍓嶇蹇呴』淇濆瓨棣栨鐢熸垚杩斿洖鐨?`thread_id`锛屽悗缁弽棣堝師鏍蜂紶鍥炪€?

### 2.3 浜哄悕 Prompt 浼樺寲

鐩爣锛氭洿绋冲畾杈撳嚭 5 涓悕瀛楋紝鍖呭惈鍑哄銆佸瘬鎰忋€佽В閲娿€?

褰撳墠瑕佹眰锛?

- 鎭板ソ 5 涓€欓€?
- 姣忎釜鍚嶅瓧蹇呴』鍖呭惈濮撴皬
- `reference` 鍐欏嚭澶勬垨鐏垫劅鏉ユ簮
- `moral` 鍚屾椂鍐欏瘬鎰忓拰瑙ｉ噴
- 浜哄悕鍦烘櫙涓嶉渶瑕佸煙鍚嶏細
  - `domain = ""`
  - `domain_status = "涓嶉€傜敤"`

### 2.4 浼佷笟鍚?Prompt 浼樺寲

鐩爣锛氱粨鍚堣涓氥€佸搧鐗岃皟鎬с€佺煡璇嗗簱鍐呭锛岀敓鎴愭洿鍍忓晢涓氬搧鐗岀殑鍚嶅瓧銆?

褰撳墠瑕佹眰锛?

- 鎭板ソ 5 涓€欓€?
- 缁撳悎琛屼笟銆佷笟鍔℃柟鍚戙€佺洰鏍囧缇ゃ€佸搧鐗岃皟鎬ф垨鏍稿績璇夋眰
- 涓诲姩鍚告敹鐢ㄦ埛鐭ヨ瘑搴撻噷鐨勪骇鍝佺壒寰併€佷紒涓氳鍒欍€佸搧鐗岀蹇屻€佸叧閿瘝鍜屽樊寮傚寲鍗栫偣
- 鍚嶅瓧瑕佸儚鐪熷疄鍟嗕笟鍝佺墝锛岃€屼笉鏄鏄庤瘝銆佹妧鏈弬鏁版垨鍙ｅ彿
- `reference` 璇存槑鍒涙剰鏉ユ簮
- `moral` 璇存槑鍝佺墝瀵撴剰鍜屽晢涓氳В閲?
- `domain` 鐢熸垚绠€鐭?`.com` 鍩熷悕寤鸿
- `domain_status` 鍏堝～鈥滄鍦ㄦ煡璇?..鈥濓紝鍚庣鍐嶇粺涓€瑕嗙洊

### 2.5 瀹犵墿/IP Prompt 浼樺寲

鐩爣锛氭洿鍙埍銆佹洿濂借銆佹洿鏈夌敾闈㈡劅銆?

褰撳墠瑕佹眰锛?

- 鎭板ソ 5 涓€欓€?
- 鍚嶅瓧鍙埍銆侀『鍙ｃ€佸鏄撳懠鍞?
- 浼樺厛 1-3 涓瓧
- 鍙娇鐢ㄥ彔闊炽€佹樀绉版劅銆佸皬鍚嶆劅銆佹嫙澹版劅銆佽交寰弽宸悓
- 缁撳悎姣涜壊銆佷綋鍨嬨€佸姩浣溿€佹€ф牸銆佷範鎯垨 IP 璁惧畾
- 姣忎釜鍚嶅瓧閮借璁╀汉鑱旀兂鍒板叿浣撶敾闈?
- 瀹犵墿/IP 鍦烘櫙涓嶉渶瑕佸煙鍚嶏細
  - `domain = ""`
  - `domain_status = "涓嶉€傜敤"`

## 3. RAG 涓庝紒涓氱煡璇嗗簱璇存槑

鐩稿叧鏂囦欢锛?

- `ainame/routers/rag_router.py`
- `ainame/core/rag_service.py`
- `ainame/rag_worker.py`
- `ainame/core/workflow.py`

褰撳墠娴佺▼锛?

1. 鍓嶇璋冪敤 `/knowledge/upload` 涓婁紶 TXT/PDF銆?
2. 鍚庣淇濆瓨鏂囦欢骞跺垱寤?`knowledge_files` 璁板綍锛屽垵濮嬬姸鎬佷负 `pending`銆?
3. 鍚庣鎶曢€?RabbitMQ 浠诲姟銆?
4. `rag_worker.py` 娑堣垂浠诲姟骞舵瀯寤虹敤鎴蜂笓灞炵煡璇嗗簱銆?
5. 浼佷笟璧峰悕鏃讹紝`company_naming_node` 浣跨敤 `user_id + other` 妫€绱㈢煡璇嗗簱鍐呭銆?
6. 妫€绱㈢粨鏋滆繘鍏ヤ紒涓氬悕 Prompt銆?

鎴愬憳 A 娉ㄦ剰锛?

- RabbitMQ 蹇呴』鍚姩銆?
- `knowledge_files` 琛ㄥ繀椤诲瓨鍦ㄣ€?
- 涓婁紶鎺ュ彛瀛楁鍚嶅浐瀹氫负 `file`銆?
- 鎴愬姛涓婁紶涓嶄唬琛ㄧ煡璇嗗簱宸茬粡鏋勫缓瀹屾垚锛屽彧浠ｈ〃浠诲姟宸插叆闃熴€?

鎴愬憳 B 娉ㄦ剰锛?

- 涓婁紶鎴愬姛鍚庝笉瑕佹彁绀衡€滃涔犲畬鎴愨€濓紝寤鸿鎻愮ず鈥滀笂浼犳垚鍔燂紝鍚庡彴澶勭悊涓€濄€?
- 浼佷笟鍚嶇敓鎴愬墠锛屽鏋滃垰涓婁紶鏂囦欢锛屽彲鑳介渶瑕佺瓑寰?worker 瀹屾垚澶勭悊銆?

## 4. 鍜屾垚鍛?A 鐨勪氦鎺ラ噸鐐?

### 4.1 鏁版嵁搴撳拰杩佺Щ褰掑睘

浠ヤ笅灞炰簬鎴愬憳 A 鑼冨洿锛?

- `user.free_quota`
- `usage_records`
- `name_records`
- `name_feedbacks`
- `knowledge_files`
- Alembic 鐗堟湰閾?
- `alembic_version` 琛ㄧ淮鎶?

鏈湴鑱旇皟鏃堕亣鍒拌繃鐨勯棶棰橈細

```text
Unknown column 'user.free_quota' in 'field list'
```

鍘熷洜锛氫唬鐮佹ā鍨嬪凡缁忔湁 `free_quota`锛屼絾 MySQL 琛ㄧ粨鏋勬湭鍗囩骇銆?

褰撳墠鏈湴鏁版嵁搴撶姸鎬佸凡缁忔墽琛屽埌锛?

```text
9c2a1f7e4d8b
```

骞跺凡瀛樺湪锛?

```text
user
email_code
name_records
name_feedbacks
usage_records
knowledge_files
```

璇存槑锛氳繖浜涜〃鍚庣画闇€瑕佷繚鐣欙紝褰撳墠涓嶈鍥為€€銆?

### 4.2 鍚庣鎺ュ彛渚濊禆

AI 宸ヤ綔娴佷緷璧栵細

- `DEEPSEEK_API_KEY`
- PostgreSQL LangGraph checkpointer锛屽綋鍓嶄唬鐮侀噷 `DB_URI = postgresql://postgres:123456@localhost:5432/ainame`
- MySQL 涓氬姟搴擄紝鐢ㄤ簬鐢ㄦ埛銆佸巻鍙层€侀搴︺€佺煡璇嗗簱鏂囦欢璁板綍
- RabbitMQ锛岀敤浜庣煡璇嗗簱寮傛浠诲姟
- Redis锛岀敤浜庨獙璇佺爜

娉ㄦ剰锛氬綋鍓?workflow 鍐呴儴鐨?LangGraph 璁板繂搴撹繛鎺ュ啓姝讳负 PostgreSQL 鍦板潃锛屽拰涓氬姟搴?`settings.DB_URI` 涓嶆槸鍚屼竴涓厤缃€傛垚鍛?A 鍚庣画鍙互鑰冭檻鎶婂畠涔熻縼鍒?`.env`銆?

## 5. 鍜屾垚鍛?B 鐨勪氦鎺ラ噸鐐?

### 5.1 璇锋眰鍦板潃

褰撳墠鍓嶇璇锋眰鍦板潃搴斾负锛?

```js
const BASE_URL = "http://127.0.0.1:8000";
```

涔嬪墠鍙戠幇杩囧啓姝诲眬鍩熺綉鍦板潃瀵艰嚧鎺ュ彛鎵撲笉閫氾細

```js
http://192.168.1.91:8000
```

鏈満鑱旇皟鏃跺簲浣跨敤 `127.0.0.1:8000` 鎴?`localhost:8000`銆?

### 5.2 鐧诲綍鍜?token

`/names/generate`銆乣/names/feedback`銆乣/knowledge/upload` 閮介渶瑕侊細

```http
Authorization: Bearer <token>
```

濡傛灉鍚庣鏃ュ織鍑虹幇锛?

```text
POST /names/generate 401 Unauthorized
```

浼樺厛妫€鏌ワ細

- 鏄惁鍏堢櫥褰?
- token 鏄惁淇濆瓨鍒?`uni` storage
- 璇锋眰澶存槸鍚︽惡甯?`Authorization`

### 5.3 鍓嶇蹇呴』浣跨敤鐨勫搷搴斿瓧娈?

棣栨鐢熸垚鍝嶅簲锛?

```json
{
  "thread_id": "...",
  "record_id": 1,
  "names": []
}
```

鍙嶉鍝嶅簲锛?

```json
{
  "thread_id": "...",
  "record_id": 1,
  "names": []
}
```

`names` 涓瘡椤瑰瓧娈碉細

```json
{
  "name": "",
  "reference": "",
  "moral": "",
  "domain": "",
  "domain_status": ""
}
```

鍓嶇灞曠ず寤鸿锛?

- 浜哄悕锛氬睍绀?`name`銆乣reference`銆乣moral`锛涢殣钘忕┖ `domain`
- 浼佷笟鍚嶏細灞曠ず `domain` 鍜?`domain_status`
- 瀹犵墿/IP锛氬睍绀?`name`銆乣reference`銆乣moral`锛涢殣钘忕┖ `domain`

## 6. 娴嬭瘯璇存槑

鏂板闈欐€?杞婚噺娴嬭瘯锛?

- `ainame/tests/test_workflow_routing.py`
- `ainame/tests/test_thread_memory.py`
- `ainame/tests/test_human_prompt.py`
- `ainame/tests/test_company_prompt.py`
- `ainame/tests/test_pet_prompt.py`

杩欎簺娴嬭瘯涓嶄細璋冪敤 DeepSeek銆丮ySQL銆丳ostgreSQL銆丷abbitMQ锛屼富瑕佺敤浜庨攣瀹氾細

- 涓夌被 category 璺敱
- 鏈煡 category 鏄庣‘鎶ラ敊
- 棣栨鐢熸垚鏂板缓 `thread_id`
- 鍙嶉澶嶇敤鏃?`thread_id`
- 涓夌被 Prompt 鐨勫叧閿害鏉?

杩愯鏂瑰紡锛?

```powershell
cd D:\python\ainameproject
conda run -n fastapi-env python -m unittest .\ainame\tests\test_pet_prompt.py .\ainame\tests\test_company_prompt.py .\ainame\tests\test_human_prompt.py .\ainame\tests\test_workflow_routing.py .\ainame\tests\test_thread_memory.py
```

鏈€杩戜竴娆＄粨鏋滐細

```text
Ran 10 tests ... OK
```

## 7. 褰撳墠宸茬煡娉ㄦ剰浜嬮」

1. `settings` 宸叉敮鎸佽嚜鍔ㄥ姞杞?`ainame/.env`銆?
2. `requirements.txt` 宸插姞鍏?`python-dotenv`銆?
3. `docs/成员B接口调用示例.md` 宸叉暣鐞嗘帴鍙ｈ姹傚拰鍝嶅簲鏍蜂緥銆?
4. 閮ㄥ垎鏃ф枃妗ｅ湪 Windows 缁堢閲屾樉绀轰贡鐮侊紝浣嗘枃浠舵湰韬寜椤圭洰鐜扮姸缁х画淇濈暀銆?
5. `/names/get_names` 鏄棫鎺ュ彛锛屼細鐢熸垚 `legacy-*` 璁板綍锛屼笉鏄帹鑽愮殑璁板繂閾捐矾銆傚缓璁垚鍛?B 浣跨敤 `/names/generate`銆?
6. 浼佷笟鍚嶄細鎵ц `.com` 鍩熷悕鏌ヨ锛岀綉缁滄垨 whois 鏈嶅姟涓嶇ǔ瀹氭椂鍙兘鎷栨參鍝嶅簲銆?

## 8. 鍚庣画寤鸿

缁欐垚鍛?A锛?

- 灏?workflow 閲岀殑 PostgreSQL checkpoint `DB_URI` 鏀逛负浠?`.env` 璇诲彇銆?
- 鏄庣‘ MySQL 涓?PostgreSQL 鐨勮亴璐ｈ竟鐣屻€?
- 妫€鏌?Alembic 鐗堟湰閾撅紝閬垮厤鍐嶅嚭鐜版暟鎹簱璁板綍浜嗕笉瀛樺湪 revision 鐨勬儏鍐点€?
- 缁?`/names/generate` 澧炲姞鏇村弸濂界殑寮傚父澶勭悊锛岄伩鍏?AI/RAG 澶栭儴渚濊禆澶辫触鏃剁洿鎺?500銆?

缁欐垚鍛?B锛?

- 鍚姩鏃跺鏋滄病鏈?token锛屽缓璁嚜鍔ㄨ烦杞櫥褰曢〉銆?
- 浼佷笟鐭ヨ瘑搴撲笂浼犳垚鍔熷悗锛屾枃妗堟敼涓衡€滀笂浼犳垚鍔燂紝鍚庡彴澶勭悊涓€濄€?
- 鍙嶉鎸夐挳鐐瑰嚮鍓嶇‘璁?`thread_id` 瀛樺湪锛屽惁鍒欐彁绀虹敤鎴峰厛鐢熸垚涓€娆°€?
- 鎸?`docs/成员B接口调用示例.md` 鑱旇皟涓夋潯涓绘帴鍙ｃ€?

缁欐垚鍛?C锛?

- 鍚庣画鍙互缁х画浼樺寲鍙嶉鍦烘櫙 Prompt锛岃浜哄悕鍜屽疇鐗╁悕涔熻兘鏇村ソ鍒╃敤鍘嗗彶缁撴灉銆?
- 浼佷笟鍚?RAG 鍙互鍔犲叆鐭ヨ瘑搴撲负绌烘椂鐨勯檷绾ф彁绀恒€?
- 缁撴瀯鍖栬緭鍑哄彲鑰冭檻鎸変笉鍚?category 鎷?schema锛岄伩鍏嶄汉鍚?瀹犵墿鍚嶄篃琚揩甯?`domain` 瀛楁銆?
