#!/bin/env python
#bili xml <==> Dplayer json converter
import sys,json
import re

# struct and vars
xmlhead0="<i><chatserver>"
xmlhead1="</chatserver><chatid>"
xmlhead2="</chatid><mission>0</mission><maxlimit>"
xmlhead3="</maxlimit><source></source><ds></ds><de></de><max_count>"
xmlhead4="</max_count><count>"
xmlhead5="</count>"
taghead="<d p=\""
tagtail="</d>"
xmltail="</i>"
btypemask={
'right':"1",
'bottom':"4",
'top':"5",
'1':"right",
'4':"bottom",
'5':"top"
}

def covj(xmlfp,jsonfp,**opt):
    data=""
    try:
        data=xmlfp.read()
        data=data.replace("</i>","")
        data=data.split('<d p=\"')
        #id=opt.get("id",data[0].split("<chatid>")[1].split("</chatid>")[0])
        id=''
        data=data[1:len(data)]
        dmp=[]
        for danmaku in data :
            res = re.findall(r'">(.*)</d>$', danmaku)
            if res:
                danmaku_content = res[0]
            else:
                danmaku_content = ''
            danmaku=danmaku.replace("\">",",").replace("</d>","").split(",")
            # time: item[0],
            # type: typeMap[item[1]],
            # color: item[2],
            # author: item[3],
            # text: item[4]
            danmaku_data=[
                float(danmaku[0]),
                btypemask.get(danmaku[1],"right"),
                ("#"+hex(int(danmaku[3])+0xff000000)[4:])[:7],
                "",
                danmaku_content,
            ]
            dmp.append(danmaku_data)
        print("done reading danmaku pool :"+str(len(dmp))+" added")
        del(data)
        jsonfp.write(json.dumps({'code':1,'danmaku':dmp}))
        return True
    except:
        print("Error:"+str(sys.exc_info()[1]))
        return False


def covx(jsonfp,xmlfp,**opt):
    try:
        #print(sds)
        dmp=json.loads(jsonfp.read(), encoding="utf-8").get("danmaku",[])
        id=opt.get("id","")
        xmlfp.write(xmlhead0+opt.get("chatserver","domain")+xmlhead1+id+xmlhead2+"1000"+xmlhead3+"1000"+xmlhead4+str(len(dmp))+xmlhead5)
        for danmaku in dmp:
            time=str(danmaku.get("time",0))
            type=btypemask.get(danmaku.get("type","right"),"1")
            size="25"
            if len(danmaku.get("color","#ffffff")) == 7:
                color=str(int(danmaku.get("color","#ffffff")[1:7],16))
            if len(danmaku.get("color","#ffffff")) == 4:
                color=str(int(danmaku.get("color")[1:2]+danmaku.get("color")[1:2]+danmaku.get("color")[2:3]+danmaku.get("color")[2:3]+danmaku.get("color")[3:4]+danmaku.get("color")[3:4],16))
            else:
                color="16777215"
            post_time=str(danmaku.get("post_time",0))
            comment=danmaku.get("text","").encode("utf-8")
            tag=taghead+time+","+type+","+size+","+color+","+post_time+","+"0,0,0\">"+comment+tagtail
            xmlfp.write(tag)
        xmlfp.write(xmltail)
        print("done saving danmaku pool")
    except:
        print("fail saving danmaku pool: "+str(sys.exc_info()[1]))


def main():
    option="normal"
    jindex=-1
    xindex=-1
    if len(sys.argv) > 1 :
        args=sys.argv[1:]
        for i in range(0,len(args)):
            if args[i].endswith(".json"):
                jpath=args[i]
                jindex=i
                continue
            if args[i].endswith(".xml"):
                xpath=args[i]
                xindex=i
                continue
            else :
                option+=","+args[i]
    if  jindex==-1 and xindex!=-1 :
        try:
            covj(open(xpath, encoding="utf-8"),open(xpath.split(".")[0]+".json","w"),id=xpath.split(".")[0])
        except:
            print("Error:"+str(sys.exc_info()[1]))
            pass
        return
    if  jindex!=-1 and xindex==-1:
        try:
            covx(open(jpath),open(jpath.split(".")[0]+".xml","w"),id=jpath.split(".")[0])
        except:
            print("Error:"+str(sys.exc_info()[1]))
            pass
        return
    if jindex>xindex :
        try:
            covj(open(xpath),open(jpath,"w"),id=jpath.split(".")[0])
        except:
            print("Error:"+str(sys.exc_info()[1]))
            pass
        return
    else:
        try:
            covx(open(jpath),open(xpath,"w"),id=xpath.split(".")[0])
        except:
            print("Error:"+str(sys.exc_info()[1]))
            pass
        return
    if  jindex==-1 and xindex==-1:
        print("not enough args")

if __name__ == "__main__":
    main()
