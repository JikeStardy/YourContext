import logging

from yourcontext.tools.video.bilibili.bilibili_video import BilibiliVideo


def main():
    import sys
    logging.basicConfig(level=logging.DEBUG)
    video_content = BilibiliVideo.get_video_content_pipeline(
        url="https://www.bilibili.com/video/BV13Sm1BYEKp",
        need_timestamp=True
    )
    with open("test.srt", "w", encoding="utf-8") as f:
        f.write(video_content.model_dump_json(ensure_ascii=False))
    # bili_client = BilibiliVideo()
    # asr_result = ASRBailian.get_asr_result(
    #     file_url=AliyunOSS().get_presign_url(object_name="BV1ppmCBVEww.mp3"),
    #     resp_mode=ASRBailian.RespMode.SRT,
    # )
    # with open("test.srt", "w", encoding="utf-8") as f:
    #     f.write(json.dumps(asr_result))


if __name__ == "__main__":
    main()
