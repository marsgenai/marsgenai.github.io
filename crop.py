import cv2
import sys
import os

def crop_video(input_path, output_path, crop_bottom):
    # 打开视频文件
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"错误：无法打开视频文件: {input_path}")
        sys.exit(1)

    # 获取视频的基本信息
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"视频信息: 宽度={frame_width}, 高度={frame_height}, 帧率={fps:.2f}, 总帧数={total_frames}")

    if total_frames == 0:
        print("警告: 视频总帧数为0，请检查输入视频文件是否有效或为空。")
        cap.release()
        sys.exit(1)
    
    if fps == 0:
        print("警告: 视频帧率(FPS)为0。这可能导致输出问题。将尝试使用默认值 25.0。")
        fps = 25.0 # 设置一个默认的FPS

    # 动态计算裁剪区域
    crop_x = 0  # 不裁剪左右
    crop_y = 0  # 不裁剪顶部
    crop_width = frame_width
    crop_height = frame_height - crop_bottom  # 裁剪掉底部 crop_bottom 像素

    if crop_height <= 0:
        print("错误：裁剪高度无效，导致裁剪后的高度小于或等于0。请检查裁剪参数。")
        cap.release() # 如果提前退出，释放捕获对象
        sys.exit(1)
    
    # 确保 VideoWriter 的帧尺寸是整数
    output_frame_width = int(crop_width)
    output_frame_height = int(crop_height)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"信息：已创建输出目录: {output_dir}")
        except OSError as e:
            print(f"错误：无法创建输出目录 {output_dir}: {e}")
            cap.release()
            sys.exit(1)

    # 设置输出视频编码器和参数
    # **重要：绿色屏幕问题通常与编解码器选择有关**
    # 尝试以下编解码器选项。如果一个不起作用，请尝试下一个。

    # 选项 1: H.264 (AVC1) - 通常是 MP4 的最佳选择，但可能需要 FFmpeg 支持
    fourcc = cv2.VideoWriter_fourcc(*'avc1') # 或者 'H264', 'X264'
    output_path_final = output_path if output_path.lower().endswith(".mp4") else output_path + ".mp4"

    # 选项 2: MP4V - 另一个常见的 MP4 编解码器
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # output_path_final = output_path if output_path.lower().endswith(".mp4") else output_path + ".mp4"
    
    # 选项 3: XVID - 非常可靠，但通常用于 .AVI 文件
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # output_path_final = os.path.splitext(output_path)[0] + ".avi" # 确保输出为 .avi
    # print("提示: 使用 XVID 编解码器, 输出文件将是 .avi 格式。")

    # 确保 fps 是浮点数，但有些编解码器可能对整数更友好
    out_fps = float(fps)
    # out_fps = int(fps) # 如果 float(fps) 有问题，可以尝试这个

    out = cv2.VideoWriter(output_path_final, fourcc, out_fps, (output_frame_width, output_frame_height))
    
    if not out.isOpened():
        print(f"错误：无法打开用于写入的输出视频文件 '{output_path_final}'。")
        print("可能的原因及解决方法:")
        print(f"1. 编解码器 '{''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])}' 不受支持或未正确安装。")
        print("   - 尝试更改脚本中的 `fourcc` 变量为其他选项 (例如，如果当前是 'mp4v'，尝试 'avc1' 或 'XVID')。")
        print("   - 如果使用 'avc1'/'H264'，确保您的 OpenCV 安装链接了 FFmpeg。")
        print("   - 如果使用 'XVID'，确保输出文件扩展名是 '.avi'。")
        print("2. 输出路径无效或程序没有写入权限。")
        print("3. 传递给 VideoWriter 的帧尺寸、FPS 可能与编解码器期望的不符。")
        cap.release()
        sys.exit(1)
    else:
        print(f"信息：输出视频文件已打开: {output_path_final} 使用编解码器: {''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])}, FPS: {out_fps}, 尺寸: ({output_frame_width}x{output_frame_height})")

    # 逐帧读取和裁剪
    current_frame_num = 0
    processed_frames_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            if current_frame_num < total_frames and total_frames > 0: 
                 print(f"警告: 视频可能提前结束或在读取第 {current_frame_num + 1} 帧时出错。预期 {total_frames} 帧，实际读取 {current_frame_num} 帧。")
            break
        
        current_frame_num += 1

        # 裁剪帧
        # 确保裁剪区域不会超出帧的边界
        # y:y+h, x:x+w
        actual_crop_height = min(output_frame_height, frame.shape[0] - crop_y)
        actual_crop_width = min(output_frame_width, frame.shape[1] - crop_x)

        if actual_crop_height <=0 or actual_crop_width <=0:
            print(f"警告: 帧 {current_frame_num} 的计算裁剪尺寸无效 ({actual_crop_width}x{actual_crop_height})。跳过此帧。")
            continue

        cropped_frame = frame[crop_y : crop_y + actual_crop_height, crop_x : crop_x + actual_crop_width]
        
        # 确保裁剪后的帧与 VideoWriter 期望的尺寸一致
        if cropped_frame.shape[0] != output_frame_height or cropped_frame.shape[1] != output_frame_width:
            # print(f"警告: 帧 {current_frame_num} 裁剪后尺寸 ({cropped_frame.shape[1]}x{cropped_frame.shape[0]}) "
            #       f"与 VideoWriter 期望尺寸 ({output_frame_width}x{output_frame_height}) 不符。将尝试调整大小。")
            try:
                # 如果尺寸不匹配，通常是因为视频最后几帧可能尺寸略有不同，或者裁剪逻辑需要更精确处理边界
                # 对于固定裁剪，理论上尺寸应该总是匹配的。如果频繁出现此警告，需检查裁剪逻辑。
                resized_cropped_frame = cv2.resize(cropped_frame, (output_frame_width, output_frame_height))
                out.write(resized_cropped_frame)
            except cv2.error as e:
                print(f"错误: 调整帧 {current_frame_num} 大小时出错: {e}. 跳过此帧。")
                continue
        else:
            out.write(cropped_frame)
        
        processed_frames_count += 1

        # 打印进度
        if processed_frames_count % 100 == 0:
            print(f"信息：已处理 {processed_frames_count}/{total_frames} 帧...")

    # 释放资源
    cap.release()
    out.release() # 非常重要，确保视频文件正确关闭和保存

    if processed_frames_count > 0:
        print(f"信息：裁剪完成，共处理了 {processed_frames_count} 帧。输出文件保存到: {output_path_final}")
        if os.path.exists(output_path_final):
             print(f"信息：输出文件大小: {os.path.getsize(output_path_final) / (1024*1024):.2f} MB")
        else:
             print(f"错误: 输出文件 {output_path_final} 未找到，可能写入失败。")

    else:
        print(f"警告：没有处理任何帧。请检查输入视频 '{input_path}' 是否为空或读取过程中出现问题。")
        if os.path.exists(output_path_final) and os.path.getsize(output_path_final) == 0:
            print(f"警告：输出文件 '{output_path_final}' 已创建但为空。这强烈暗示编解码器或写入参数问题。")
        elif not os.path.exists(output_path_final):
            print(f"错误: 输出文件 '{output_path_final}' 未创建。")


if __name__ == "__main__":
    # --- 配置参数 ---
    input_video = "static/videos/first7.mp4"  # 替换为您的输入视频路径
    
    # 建议：将输出文件名与选择的编解码器类型匹配
    # 如果使用 'avc1' 或 'mp4v', 通常使用 .mp4
    # 如果使用 'XVID', 通常使用 .avi
    output_video_base = "static/videos/first/first7" # 基本文件名，扩展名会根据编解码器调整
    
    crop_bottom_pixels = 5  # 要从底部裁剪掉的像素数量
    # --- 配置结束 ---


    # 检查输入文件是否存在
    if not os.path.exists(input_video):
        print(f"错误：输入视频文件不存在: {input_video}")
        sys.exit(1)
    
    # 根据选择的编解码器（在 crop_video 函数内部设置）来决定输出文件名
    # 这里只是一个示例，实际的文件名会在函数内根据选定的 fourcc 确定或调整
    # 为了简单起见，我们这里先假设输出是 mp4
    final_output_path = output_video_base + ".mp4" 
    # 如果在函数内部选择 XVID，它会被改为 .avi

    crop_video(input_video, final_output_path, crop_bottom_pixels)
    

    print("\n--- 故障排除提示 ---")
    print("如果视频仍然是绿色或无法播放:")
    print("1. **更改编解码器(FourCC)**: 编辑脚本中的 `fourcc = cv2.VideoWriter_fourcc(*'...')` 行。")
    print("   - 尝试 `'avc1'` (H.264, MP4 的好选择, 可能需要 FFmpeg)。")
    print("   - 尝试 `'mp4v'` (MP4 的另一个选项)。")
    print("   - 尝试 `'XVID'` (AVI 的可靠选择, 记得将输出文件名改为 .avi)。")
    print("2. **检查 OpenCV 的 FFmpeg 支持**: 如果使用 H.264 等编解码器，OpenCV 可能需要 FFmpeg。")
    print("   `print(cv2.getBuildInformation())` 可以查看相关信息，寻找 FFMPEG YES。")
    print("3. **检查输入视频**: 确保输入视频本身没有问题，可以用普通播放器播放。")
    print("4. **帧率(FPS)**: 尝试将 `out_fps = float(fps)` 改为 `out_fps = int(fps)`。")
    print("5. **权限问题**: 确保脚本有权限在输出路径创建和写入文件。")
    print("6. **查看控制台的详细错误/警告信息**。")
