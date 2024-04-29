# igpp : Instagram Profile Picture Downloader  

## Features  
- **lite and easy to use** keeping it simple.  
- **caching** skips already downloaded photos.  
- **public/private** both are supported.  
- **Fast mode** (320px) will speed up your research,  
  (this skips 2nd GET request) thus, saves time  
  still better than Instagram's default 150x150 `(-_-)`   

## Requirements:  
`pip install httpx[http2]`  
`pip install browser_cookie3`  # Optional  

## Gettings Started (Setup):  
0. Login to instagram.com web.  
1. open Developer tools, goto Network Tab (reload [ctrl+r] to capture traffic)  
2. search for username in IG's search box  
3. search "graphql" in Network Tab's search box  
4. find POST request to /api/graphql/, right click, copy as curl.  
it **must** contains this key:value in payload/data  
`'variables': '{"data":{"context":"blended","include_reel":"true","query":"mrbeast","rank_token":"","search_surface":"web_top_search"},"hasQuery":true}',`   
5. goto https://curlconverter.com, paste it there     
copy output, paste it in this file `secrets_session.py`  
6. DO NOT share `secrets_session.py`   
Note: this `secrets_session.py` seems to be stop working after sometime (days/hours),  
  you may have to redo this everytime your session expires / logs out.  


## Usage:  
  `python igpp.py -i apple android instagram mrbeast`   
**Fast mode:**   
  `python igpp.py -f -i apple instagram mrbeast`  
**Search mode:** search and show count=10, default: 5  
  `python igpp.py -s -c 10 -i apple instagram mrbeast`  
**No Download:**  
  `python igpp.py -s -c 10 -n -i apple instagram mrbeast`  
**help:**  
  `python igpp.py --help/-h`  

*(-_-)* after pushing this script, came across a HUGE & more advanced library [Instaloader]  
  what a timing!   

## Todo:  
- make headers/cookies process simple:  
	
