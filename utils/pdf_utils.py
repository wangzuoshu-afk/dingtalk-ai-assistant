"""
PDF生成工具
使用ReportLab生成专业格式的PDF报告
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime
from typing import Optional


class PDFGenerator:
    """PDF生成器类"""
    
    def __init__(self, output_dir: str = '/tmp'):
        """
        初始化PDF生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 注册中文字体（使用系统自带字体）
        try:
            # 尝试注册常见的中文字体
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/System/Library/Fonts/PingFang.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Chinese', font_path))
                    self.has_chinese_font = True
                    break
            else:
                self.has_chinese_font = False
        except:
            self.has_chinese_font = False
    
    def _get_styles(self):
        """获取样式"""
        styles = getSampleStyleSheet()
        
        # 如果有中文字体，使用中文字体
        font_name = 'Chinese' if self.has_chinese_font else 'Helvetica'
        
        # 标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # 一级标题样式
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # 二级标题样式
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=10
        )
        
        # 正文样式
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontName=font_name,
            fontSize=11,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )
        
        return {
            'title': title_style,
            'heading1': heading1_style,
            'heading2': heading2_style,
            'body': body_style
        }
    
    def generate_report_pdf(self, content: str, title: str = "AI报告") -> str:
        """
        生成PDF报告
        
        Args:
            content: Markdown格式的报告内容
            title: 报告标题
            
        Returns:
            str: 生成的PDF文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 获取样式
        styles = self._get_styles()
        
        # 构建文档内容
        story = []
        
        # 添加标题
        story.append(Paragraph(title, styles['title']))
        story.append(Spacer(1, 0.5*cm))
        
        # 添加生成时间
        date_text = f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}"
        story.append(Paragraph(date_text, styles['body']))
        story.append(Spacer(1, 1*cm))
        
        # 解析Markdown内容并添加到PDF
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.3*cm))
                continue
            
            # 处理标题
            if line.startswith('# '):
                text = line[2:].strip()
                story.append(Paragraph(text, styles['heading1']))
            elif line.startswith('## '):
                text = line[3:].strip()
                story.append(Paragraph(text, styles['heading2']))
            elif line.startswith('### '):
                text = line[4:].strip()
                story.append(Paragraph(text, styles['heading2']))
            # 处理列表
            elif line.startswith('- ') or line.startswith('* '):
                text = '• ' + line[2:].strip()
                story.append(Paragraph(text, styles['body']))
            elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
                story.append(Paragraph(line, styles['body']))
            # 处理普通段落
            else:
                # 替换Markdown粗体标记
                text = line.replace('**', '<b>').replace('**', '</b>')
                text = text.replace('*', '<i>').replace('*', '</i>')
                story.append(Paragraph(text, styles['body']))
        
        # 生成PDF
        try:
            doc.build(story)
            return filepath
        except Exception as e:
            raise Exception(f"生成PDF失败：{str(e)}")
    
    def generate_simple_pdf(self, text: str, filename: Optional[str] = None) -> str:
        """
        生成简单的文本PDF
        
        Args:
            text: 文本内容
            filename: 文件名（可选）
            
        Returns:
            str: 生成的PDF文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"document_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = self._get_styles()
        story = []
        
        # 分段处理文本
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), styles['body']))
                story.append(Spacer(1, 0.5*cm))
        
        doc.build(story)
        return filepath
