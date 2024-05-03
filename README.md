# igpp : Instagram Profile Picture Downloader  
An utility to download high quality instagram profile picture.  

## Usage:
```bash
python igpp.py apple trevorwallace ... 
```

## Requirements:  
`pip install httpx`  
**secrets_session.py** *(see below)*


## Gettings Started (Setup):  
0. Login to instagram.com web.  
1. open Developer tools, goto Network Tab (reload [ctrl+r] to capture traffic)  
2. search for username in IG's search box  
3. search "graphql" in Network Tab's search box  
4. find POST request to /api/graphql/, right click, copy as curl.  
it **must** contain `query` in variables key  
`'variables': '{"data":{"context":"blended","include_reel":"true","query":"apple",...',`   
5. goto https://curlconverter.com, paste it there     
copy output, paste it in this file `secrets_session.py`  
6. DO NOT share `secrets_session.py`   
Note: this `secrets_session.py` seems to be stop working after sometime (days/hours),  
  depends upon how often / how many requests you make.  
  you may have to redo this everytime your session expires / logs out.  


## Advanced Version:  
### Usage:  
  `python advance_igpp.py -i apple android instagram mrbeast`   
**Fast mode:** 320x320px   
  `python advance_igpp.py -f -i apple instagram mrbeast`  
**Search mode:** search and show count=10, default: 5  
  `python advance_igpp.py -s -c 10 -i apple instagram mrbeast`  
**help:**  
  `python advance_igpp.py --help/-h`  


## Todo:  
- make headers/cookies process simple   
	
## Contribute:
Any help is appreciated!