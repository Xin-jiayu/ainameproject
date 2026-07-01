# 鎴愬憳 B 鎺ュ彛璋冪敤绀轰緥

鍩虹鍦板潃绀轰緥锛歚http://127.0.0.1:8000`

鎵€鏈夋帴鍙ｉ兘闇€瑕佺櫥褰曟€侊細

```http
Authorization: Bearer <access_token>
```

## 1. 棣栨璧峰悕

`POST /names/generate`

璇存槑锛氬垱寤轰竴涓柊鐨勮捣鍚嶄换鍔°€傛垚鍔熷悗浼氭墸 1 娆″厤璐归搴︼紝鍐欏叆璧峰悕璁板綍锛屽苟杩斿洖鏂扮殑 `thread_id`銆傚悗缁弽棣堝繀椤诲鐢ㄨ繖涓?`thread_id`銆?

### 璇锋眰绀轰緥锛氫紒涓氬悕

```http
POST http://127.0.0.1:8000/names/generate
Accept: application/json
Content-Type: application/json
Authorization: Bearer <access_token>
```

```json
{
  "category": "浼佷笟鍚?,
  "surname": "",
  "gender": "涓嶉檺",
  "length": "鍥涗釜瀛椾互鍐?,
  "other": "涓€瀹跺仛鐜繚鏂版潗鏂欑殑鍒濆垱鍏徃锛屽笇鏈涘悕瀛楁湁绉戞妧鎰熴€佸彲淇¤禆",
  "exclude": ["搴?, "鏃?]
}
```

### 璇锋眰绀轰緥锛氫汉鍚?

```json
{
  "category": "浜哄悕",
  "surname": "鏋?,
  "gender": "濂?,
  "length": "涓や釜瀛?,
  "other": "甯屾湜娓╂煍銆佹湁涔﹀嵎姘旓紝閫傚悎瀹濆疂璧峰悕",
  "exclude": ["钀?]
}
```

### 璇锋眰绀轰緥锛氬疇鐗╁悕

```json
{
  "category": "瀹犵墿鍚?,
  "surname": "",
  "gender": "涓嶉檺",
  "length": "涓や釜瀛?,
  "other": "涓€鍙椿娉肩殑鐧借壊灏忕嫍锛屼翰浜恒€佺埍鎾掑▏",
  "exclude": []
}
```

### 鎴愬姛鍝嶅簲绀轰緥

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "record_id": 12,
  "names": [
    {
      "name": "闈掑矚鏉愮",
      "reference": "闈掑矚鍙栨竻鏂拌嚜鐒朵箣鎰忥紝鏉愮浣撶幇鏂版潗鏂欑鎶€灞炴€?,
      "moral": "瀵撴剰浼佷笟浠ョ豢鑹叉潗鏂欒繛鎺ョ鎶€涓庤嚜鐒?,
      "domain": "qinglancai.com",
      "domain_status": "鏈敞鍐?
    }
  ]
}
```

### 甯歌閿欒

```json
{
  "detail": "鍏嶈垂鐢熸垚娆℃暟宸茬敤瀹岋紝鏆傛椂鏃犳硶鏂板缓璧峰悕浠诲姟"
}
```

璇存槑锛欻TTP 鐘舵€佺爜 `403`銆?

```json
{
  "detail": "鏈煡璧峰悕鍒嗙被: '娓告垙瑙掕壊'锛屽厑璁稿€? 浜哄悕銆佷紒涓氬悕銆佸疇鐗╁悕"
}
```

璇存槑锛氬墠绔紶浜嗕笉鏀寔鐨?`category`銆?

## 2. 澶氳疆鍙嶉浼樺寲

`POST /names/feedback`

璇存槑锛氬熀浜庡凡鏈?`thread_id` 缁х画浼樺寲锛屼笉鎵ｅ厤璐归搴︺€傛帴鍙ｄ細璇诲彇鏃ц褰曞苟澶嶇敤鍘熸潵鐨?LangGraph 璁板繂銆?

### 璇锋眰绀轰緥

```http
POST http://127.0.0.1:8000/names/feedback
Accept: application/json
Content-Type: application/json
Authorization: Bearer <access_token>
```

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "category": "浼佷笟鍚?,
  "feedback": "鎴戝枩娆笂涓€杞殑鈥滈潚宀氭潗绉戔€濄€傝淇濈暀娓呮柊銆佺豢鑹茬殑鎰熻锛屼絾鍚嶅瓧鍐嶇煭涓€鐐癸紝鏇撮€傚悎鍝佺墝浼犳挱銆?
}
```

`category` 鍙紶锛屼篃鍙笉浼狅紱涓嶄紶鏃跺悗绔細浣跨敤璇?`thread_id` 瀵瑰簲璁板綍閲岀殑 `category`銆?

### 鎴愬姛鍝嶅簲绀轰緥

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "record_id": 12,
  "names": [
    {
      "name": "闈掑矚",
      "reference": "寤剁画涓婁竴杞潚宀氭潗绉戜腑鐨勬牳蹇冩剰璞?,
      "moral": "琛ㄨ揪娓呮磥銆佽嚜鐒躲€佸悜涓婄殑鍝佺墝姘旇川",
      "domain": "qinglan.com",
      "domain_status": "宸叉敞鍐?
    }
  ]
}
```

### 甯歌閿欒

```json
{
  "detail": "璧峰悕璁板綍涓嶅瓨鍦紝鏃犳硶缁х画浼樺寲"
}
```

璇存槑锛欻TTP 鐘舵€佺爜 `404`銆傞€氬父鏄?`thread_id` 閿欒銆佽褰曞凡鍒犻櫎锛屾垨璇ヨ褰曚笉灞炰簬褰撳墠鐧诲綍鐢ㄦ埛銆?

## 3. 浼佷笟鐭ヨ瘑搴撲笂浼?

`POST /knowledge/upload`

璇存槑锛氫笂浼犱紒涓氫笓灞炲弬鑰冩枃浠躲€傚綋鍓嶅弬鏁板悕鍥哄畾涓?`file`锛岃姹傜被鍨嬩负 `multipart/form-data`銆備笂浼犳垚鍔熷悗浼氭妸瑙ｆ瀽浠诲姟鎶曢€掑埌 RabbitMQ锛屽悗鍙板紓姝ユ瀯寤虹煡璇嗗簱銆?

### 璇锋眰绀轰緥锛歝url

```bash
curl -X POST "http://127.0.0.1:8000/knowledge/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@./company_rules.txt"
```

### 璇锋眰绀轰緥锛欻TTP 鏂囦欢

```http
POST http://127.0.0.1:8000/knowledge/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data; boundary=WebAppBoundary

--WebAppBoundary
Content-Disposition: form-data; name="file"; filename="company_rules.txt"
Content-Type: text/plain

< ./company_rules.txt
--WebAppBoundary--
```

### 鎴愬姛鍝嶅簲绀轰緥

```json
{
  "result": "success",
  "knowledge_file_id": 3,
  "status": "pending",
  "message": "鏂囦欢 company_rules.txt 涓婁紶鎴愬姛锛佸悗鍙版鍦ㄤ负鎮ㄦ瀯寤轰笓灞炵煡璇嗗簱锛岃绋嶅€欐祴璇曡捣鍚嶅姛鑳姐€?
}
```

### 甯歌閿欒

```json
{
  "detail": "Not authenticated"
}
```

璇存槑锛氱己灏戞垨浼犻敊 `Authorization`銆?

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

璇存槑锛氳〃鍗曞瓧娈靛悕涓嶆槸 `file`锛屾垨娌℃湁鐪熸涓婁紶鏂囦欢銆?

## 瀛楁绾﹀畾

`/names/generate` 璇锋眰瀛楁锛?

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
| --- | --- | --- | --- |
| `category` | string | 鏄?| 浠呮敮鎸?`浜哄悕`銆乣浼佷笟鍚峘銆乣瀹犵墿鍚峘 |
| `surname` | string | 浜哄悕蹇呭～ | 浜哄悕璧峰悕鏃跺繀椤讳紶濮撴皬 |
| `gender` | string | 鍚?| `涓嶉檺`銆乣鐢穈銆乣濂砢 |
| `length` | string | 鍚?| 鍚嶅瓧闀垮害瑕佹眰 |
| `other` | string | 鍚?| 涓氬姟闇€姹傘€佹€ф牸鐗瑰緛銆侀鏍煎亸濂界瓑 |
| `exclude` | string[] | 鍚?| 閬胯瀛楀垪琛?|

`/names/feedback` 璇锋眰瀛楁锛?

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
| --- | --- | --- | --- |
| `thread_id` | string | 鏄?| 棣栨璧峰悕杩斿洖鐨?`thread_id` |
| `category` | string | 鍚?| 涓嶄紶鏃朵娇鐢ㄥ巻鍙茶褰曠殑鍒嗙被 |
| `feedback` | string | 鏄?| 鏈疆淇敼鎰忚 |
