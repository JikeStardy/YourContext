import json
import logging

from tqdm import tqdm
from yourcontext.agents.sub_agents import video_agent
import random
import time


def main():
    logging.basicConfig(level=logging.INFO)

    with open("bilibili_video_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    idx = 0
    for video_title, bv_id in tqdm(data.items(), desc="处理视频"):
        # 休息一下
        sleep_seconds = random.randint(60, 180) if (idx + 1) % 10 != 0 else random.randint(300, 600)
        time.sleep(sleep_seconds)
        # 调用video_agent获取特定BV号下的信息
        try:
            result =  video_agent.invoke({
                "messages": [{"role": "user", "content": f"分析这个视频: {bv_id}"}]
            })
            
            analyze_content = result["messages"][-1].content

            with open(f"./temp/bilibili/{bv_id}_{video_title}.md", "w", encoding="utf-8") as f:
                f.write(analyze_content)
                
        except Exception as e:
            logging.info(f"获取视频信息时出错: {e}", exc_info=True)
        

if __name__ == "__main__":
    main()
