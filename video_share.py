import os
import subprocess
import qrcode
from pathlib import Path
import shutil
import sys
from datetime import datetime

class GitLFSVideoShare:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.videos_dir = self.repo_path / 'videos'
        self.pages_dir = self.repo_path / 'pages'
        self.setup_repository()

    def setup_repository(self):
        """初始化或检查仓库设置"""
        try:
            self.videos_dir.mkdir(exist_ok=True)
            self.pages_dir.mkdir(exist_ok=True)
            os.chdir(self.repo_path)

        except Exception as e:
            print(f"仓库设置失败: {str(e)}")
            sys.exit(1)

    def _run_command(self, command):
        """运行Git命令"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            output, error = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"命令失败: {error}")
            return output.strip()
            
        except Exception as e:
            print(f"命令执行错误: {str(e)}")
            return ""

    def create_player_page(self, video_path, title):
        """创建视频播放页面"""
        # 生成安全的文件名
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        video_relative_path = f'../videos/{safe_title}'
        
        html_content = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #fff;
        }}
        .video-container {{
            width: 100%;
            max-width: 1920px;
            margin: 20px auto;
            padding: 0 20px;
        }}
        video {{
            width: 100%;
            max-height: 85vh;
        }}
    </style>
</head>
<body>
    <div class="video-container">
        <video controls preload="metadata">
            <source src="{video_relative_path}" type="video/mp4">
        </video>
    </div>
</body>
</html>
'''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        page_name = f'{timestamp}_{safe_title}.html'
        page_path = self.pages_dir / page_name
        
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return page_path

    def share_video(self, video_path):
        try:
            # 使用安全的文件名
            original_name = Path(video_path).name
            safe_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
            target_path = self.videos_dir / safe_name

            # 复制视频文件
            print(f"复制视频文件...")
            shutil.copy2(video_path, target_path)

            # 创建播放页面
            print("创建播放页面...")
            page_path = self.create_player_page(target_path, Path(safe_name).stem)

            # 提交到Git
            print("提交到Git...")
            self._run_command(['git', 'add', str(target_path)])
            self._run_command(['git', 'add', str(page_path)])
            self._run_command(['git', 'commit', '-m', f'Add video: {safe_name}'])

            # 生成URL
            repo_url = "https://estellalin21.github.io/camforu"
            relative_path = str(page_path.relative_to(self.repo_path))
            page_url = f"{repo_url}/{relative_path.replace(chr(92), '/')}"

            # 生成二维码
            print("生成二维码...")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(page_url)
            qr.make(fit=True)
            
            qr_path = self.repo_path / 'qrcodes' / f'{Path(safe_name).stem}_qr.png'
            qr_path.parent.mkdir(exist_ok=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image.save(qr_path)

            return {
                'video_path': str(target_path),
                'page_path': str(page_path),
                'page_url': page_url,
                'qr_path': str(qr_path)
            }

        except Exception as e:
            raise Exception(f"分享失败: {str(e)}")

def main():
    print("=== GitHub LFS 视频分享工具 ===\n")
    
    try:
        # 获取仓库路径
        repo_path = os.getcwd()  # 直接使用当前目录
        print(f"使用当前目录作为仓库路径: {repo_path}")
            
        # 创建分享器
        sharer = GitLFSVideoShare(repo_path)
        
        # 获取视频文件路径
        video_path = input("\n请输入视频文件路径（直接拖入文件即可）: ").strip().strip('"')
        if not os.path.exists(video_path):
            print("错误：视频文件不存在！")
            return
        
        # 分享视频
        print("\n处理中...")
        info = sharer.share_video(video_path)
        
        print("\n=== 分享成功！===")
        print(f"视频路径: {info['video_path']}")
        print(f"播放页面: {info['page_path']}")
        print(f"访问地址: {info['page_url']}")
        print(f"二维码位置: {info['qr_path']}")
        print("\n注意：需要手动push到GitHub才能访问")
        print("运行: git push origin main")
        
    except Exception as e:
        print(f"\n错误：{str(e)}")

if __name__ == "__main__":
    main()
