// 校桥 CampusBridge 开题汇报 PPT 生成脚本
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaBook, FaComments, FaUsers, FaExchangeAlt, FaUserShield,
  FaSearch, FaUpload, FaDownload, FaEye, FaStar,
  FaThumbsUp, FaBookmark, FaBullhorn, FaHandshake, FaCommentDots,
  FaUserPlus, FaUserCheck, FaShoppingCart, FaCheckCircle,
  FaClock, FaSyncAlt, FaLightbulb, FaShieldAlt, FaCloud, FaMobileAlt,
  FaCode, FaDatabase, FaServer, FaPython, FaFlask, FaReact,
  FaCalendarAlt, FaCheck, FaRocket, FaChartLine, FaGraduationCap,
  FaUniversity, FaBriefcase, FaFileAlt, FaUserCircle, FaBell, FaCog
} = require("react-icons/fa");

// 颜色配置：Ocean Gradient 主题
const C = {
  deep: "065A82",      // 主色 - 深海蓝
  teal: "1C7293",      // 次色 - 青色
  midnight: "21295C",  // 深夜蓝
  light: "F0F9FF",     // 浅冰蓝
  accent: "F59E0B",    // 点缀色 - 琥珀
  white: "FFFFFF",
  gray: "64748B",
  lightGray: "E2E8F0",
  text: "1E293B",
  textLight: "475569",
  success: "10B981",
  coral: "F96167"
};

const FONT_HEADER = "Microsoft YaHei";
const FONT_BODY = "Microsoft YaHei";

// 渲染图标为 base64
async function icon(IconComponent, color = "#" + C.deep, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

function makeShadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.12 };
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
  pres.title = "校桥 CampusBridge 开题汇报";
  pres.author = "校桥项目组";

  const W = 13.3, H = 7.5;

  // ============ 第 1 页：封面 ============
  let s1 = pres.addSlide();
  s1.background = { color: C.midnight };

  // 装饰：左侧大色块
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.5, h: H,
    fill: { color: C.deep }, line: { type: "none" }
  });
  // 装饰圆形
  s1.addShape(pres.shapes.OVAL, {
    x: 0.5, y: 0.5, w: 0.6, h: 0.6,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s1.addShape(pres.shapes.OVAL, {
    x: 3.2, y: 6.2, w: 1.0, h: 1.0,
    fill: { color: C.teal, transparency: 60 }, line: { type: "none" }
  });
  s1.addShape(pres.shapes.OVAL, {
    x: -0.5, y: 5.5, w: 1.5, h: 1.5,
    fill: { color: C.accent, transparency: 75 }, line: { type: "none" }
  });

  // 桥型图标（用大圆+连接线表达）
  s1.addShape(pres.shapes.OVAL, {
    x: 1.4, y: 2.4, w: 0.7, h: 0.7,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s1.addShape(pres.shapes.OVAL, {
    x: 2.4, y: 2.4, w: 0.7, h: 0.7,
    fill: { color: C.white }, line: { type: "none" }
  });
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 1.7, y: 2.7, w: 1.0, h: 0.08,
    fill: { color: C.white }, line: { type: "none" }
  });
  s1.addText("校桥", {
    x: 0.5, y: 3.4, w: 3.5, h: 0.7, margin: 0,
    fontSize: 44, bold: true, color: C.white, fontFace: FONT_HEADER, align: "center"
  });
  s1.addText("CampusBridge", {
    x: 0.5, y: 4.1, w: 3.5, h: 0.4, margin: 0,
    fontSize: 18, color: C.accent, fontFace: "Consolas", align: "center", charSpacing: 4
  });
  s1.addText("校园资源交换与交流平台", {
    x: 0.5, y: 4.6, w: 3.5, h: 0.3, margin: 0,
    fontSize: 12, color: C.lightGray, fontFace: FONT_BODY, align: "center"
  });

  // 右侧文字
  s1.addText("开题汇报", {
    x: 5.2, y: 2.2, w: 7.5, h: 0.9, margin: 0,
    fontSize: 56, bold: true, color: C.white, fontFace: FONT_HEADER
  });
  s1.addText("Proposal Defense Presentation", {
    x: 5.2, y: 3.1, w: 7.5, h: 0.4, margin: 0,
    fontSize: 16, italic: true, color: C.accent, fontFace: "Consolas", charSpacing: 3
  });

  // 右侧装饰条
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 3.7, w: 0.8, h: 0.05,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s1.addText("连接每一份知识，分享每一份价值", {
    x: 5.2, y: 3.9, w: 7.5, h: 0.4, margin: 0,
    fontSize: 18, color: C.lightGray, fontFace: FONT_BODY, charSpacing: 2
  });

  // 底部信息
  s1.addText([
    { text: "汇报人：", options: { color: C.gray, fontSize: 14 } },
    { text: "项目负责人  ", options: { color: C.white, fontSize: 14, bold: true, breakLine: true } },
    { text: "指导教师：", options: { color: C.gray, fontSize: 14 } },
    { text: "指导教师  ", options: { color: C.white, fontSize: 14, bold: true, breakLine: true } },
    { text: "汇报日期：", options: { color: C.gray, fontSize: 14 } },
    { text: "2026 年 7 月", options: { color: C.white, fontSize: 14, bold: true } }
  ], { x: 5.2, y: 5.8, w: 7.5, h: 1.4, fontFace: FONT_BODY, paraSpaceAfter: 4 });

  // ============ 第 2 页：目录 ============
  let s2 = pres.addSlide();
  s2.background = { color: C.white };

  s2.addText("CONTENTS", {
    x: 0.5, y: 0.5, w: 12, h: 0.4, margin: 0,
    fontSize: 14, color: C.deep, fontFace: "Consolas", charSpacing: 8
  });
  s2.addText("汇报内容", {
    x: 0.5, y: 0.9, w: 12, h: 0.7, margin: 0,
    fontSize: 36, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.7, w: 0.6, h: 0.05,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const tocItems = [
    { num: "01", title: "现实意义与创新性", subtitle: "Significance & Innovation", color: C.deep },
    { num: "02", title: "功能描述", subtitle: "Function Description", color: C.teal },
    { num: "03", title: "可行性分析", subtitle: "Feasibility Analysis", color: C.success },
    { num: "04", title: "技术路线与进度安排", subtitle: "Technical Route & Schedule", color: C.accent },
    { num: "05", title: "预期成果", subtitle: "Expected Outcomes", color: C.coral }
  ];

  tocItems.forEach((item, i) => {
    const x = 0.7 + i * 2.5;
    // 序号大色块
    s2.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 2.8, w: 2.2, h: 3.0,
      fill: { color: item.color }, line: { type: "none" }
    });
    // 顶部白色装饰条
    s2.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 2.8, w: 2.2, h: 0.1,
      fill: { color: C.white, transparency: 60 }, line: { type: "none" }
    });
    s2.addText(item.num, {
      x: x, y: 3.0, w: 2.2, h: 1.2, margin: 0,
      fontSize: 60, bold: true, color: C.white, fontFace: "Consolas", align: "center"
    });
    s2.addText(item.title, {
      x: x + 0.1, y: 4.4, w: 2.0, h: 0.6, margin: 0,
      fontSize: 18, bold: true, color: C.white, fontFace: FONT_HEADER, align: "center"
    });
    s2.addText(item.subtitle, {
      x: x + 0.1, y: 5.0, w: 2.0, h: 0.3, margin: 0,
      fontSize: 10, color: C.white, fontFace: "Consolas", align: "center", italic: true
    });
    // 底部小图标
    s2.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.9, y: 5.4, w: 0.4, h: 0.05,
      fill: { color: C.white }, line: { type: "none" }
    });
  });

  // 页脚
  s2.addText("校桥 CampusBridge · 开题汇报", {
    x: 0.5, y: 7.0, w: 12, h: 0.3, margin: 0,
    fontSize: 10, color: C.gray, fontFace: FONT_BODY
  });

  // ============ 第 3 页：分隔页 01 ============
  let s3 = pres.addSlide();
  s3.background = { color: C.midnight };
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 7.5,
    fill: { color: C.midnight }, line: { type: "none" }
  });
  s3.addShape(pres.shapes.OVAL, {
    x: 10.5, y: -1, w: 4, h: 4,
    fill: { color: C.deep, transparency: 60 }, line: { type: "none" }
  });
  s3.addShape(pres.shapes.OVAL, {
    x: -1, y: 5, w: 3, h: 3,
    fill: { color: C.teal, transparency: 70 }, line: { type: "none" }
  });
  s3.addText("PART 01", {
    x: 0.5, y: 2.5, w: 12, h: 0.5, margin: 0,
    fontSize: 18, color: C.accent, fontFace: "Consolas", charSpacing: 6
  });
  s3.addText("现实意义与创新性", {
    x: 0.5, y: 3.0, w: 12, h: 1.0, margin: 0,
    fontSize: 54, bold: true, color: C.white, fontFace: FONT_HEADER
  });
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.1, w: 1.0, h: 0.06,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s3.addText("Why CampusBridge？", {
    x: 0.5, y: 4.3, w: 12, h: 0.4, margin: 0,
    fontSize: 20, italic: true, color: C.lightGray, fontFace: "Consolas"
  });

  // ============ 第 4 页：现实意义 - 痛点 ============
  let s4 = pres.addSlide();
  s4.background = { color: C.white };

  s4.addText("现实意义", {
    x: 0.5, y: 0.4, w: 8, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s4.addText("现有校园资源流通的四大痛点", {
    x: 0.5, y: 1.05, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s4.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const pains = [
    { icon: FaBook, title: "资料分散", desc: "学习资料散落在网盘、微信群、QQ群中，难以集中检索与沉淀", color: C.deep },
    { icon: FaBullhorn, title: "组队困难", desc: "竞赛信息靠朋友圈口口相传，跨院系组队缺乏统一渠道", color: C.teal },
    { icon: FaExchangeAlt, title: "教材浪费", desc: "毕业季大量二手教材闲置，新生却高价买新书，资源错配严重", color: C.accent },
    { icon: FaComments, title: "讨论松散", desc: "学习讨论混在微信聊天中，问题无法沉淀为可检索的知识", color: C.coral }
  ];

  pains.forEach(async (p, i) => {
    // 实际中用同步方式
  });

  // 同步生成图标并放置
  for (let i = 0; i < pains.length; i++) {
    const p = pains[i];
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.5 + col * 6.3, y = 1.9 + row * 2.5;
    // 卡片背景
    s4.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 6.0, h: 2.2,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    // 左侧色条
    s4.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 0.15, h: 2.2,
      fill: { color: p.color }, line: { type: "none" }
    });
    // 图标
    const iconData = await icon(p.icon, "#" + p.color, 256);
    s4.addImage({ data: iconData, x: x + 0.5, y: y + 0.4, w: 0.9, h: 0.9 });
    // 标题
    s4.addText(p.title, {
      x: x + 1.7, y: y + 0.3, w: 4.0, h: 0.5, margin: 0,
      fontSize: 20, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    // 描述
    s4.addText(p.desc, {
      x: x + 1.7, y: y + 0.85, w: 4.0, h: 1.2, margin: 0,
      fontSize: 12, color: C.textLight, fontFace: FONT_BODY, valign: "top"
    });
  }

  // ============ 第 5 页：创新点 ============
  let s5 = pres.addSlide();
  s5.background = { color: C.white };

  s5.addText("创新性", {
    x: 0.5, y: 0.4, w: 8, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s5.addText("四大创新打造一体化校园资源生态", {
    x: 0.5, y: 1.05, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const innovations = [
    { num: "01", icon: FaLightbulb, title: "一体化平台", desc: "首次将资料、论坛、组队、教材四大场景整合到统一系统，打破信息孤岛", color: C.deep },
    { num: "02", icon: FaUserShield, title: "校园身份认证", desc: "基于学号/工号的注册体系，确保用户真实身份，构建可信校园社区", color: C.teal },
    { num: "03", icon: FaShieldAlt, title: "RBAC 权限模型", desc: "普通用户/管理员双角色，兼顾开放共享与平台治理的双重需求", color: C.success },
    { num: "04", icon: FaCloud, title: "云存储+本地降级", desc: "默认对接腾讯云 COS 弹性存储，无密钥时自动降级到本地存储，开箱即用", color: C.accent }
  ];

  for (let i = 0; i < innovations.length; i++) {
    const it = innovations[i];
    const x = 0.5 + i * 3.2;
    // 顶部色块
    s5.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.9, h: 4.3,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    // 顶部大色条
    s5.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.9, h: 0.8,
      fill: { color: it.color }, line: { type: "none" }
    });
    // 序号
    s5.addText(it.num, {
      x: x + 0.2, y: 2.0, w: 1.0, h: 0.6, margin: 0,
      fontSize: 32, bold: true, color: C.white, fontFace: "Consolas"
    });
    // 图标
    const iconData = await icon(it.icon, "#FFFFFF", 256);
    s5.addImage({ data: iconData, x: x + 2.0, y: 2.1, w: 0.5, h: 0.5 });
    // 标题
    s5.addText(it.title, {
      x: x + 0.2, y: 2.95, w: 2.5, h: 0.5, margin: 0,
      fontSize: 18, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    // 分隔线
    s5.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: 3.55, w: 0.4, h: 0.03,
      fill: { color: it.color }, line: { type: "none" }
    });
    // 描述
    s5.addText(it.desc, {
      x: x + 0.2, y: 3.7, w: 2.5, h: 2.3, margin: 0,
      fontSize: 12, color: C.textLight, fontFace: FONT_BODY, valign: "top"
    });
  }

  // 底部结论
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 6.4, w: 12.3, h: 0.6,
    fill: { color: C.midnight }, line: { type: "none" }
  });
  s5.addText("从「各自为战」到「一站式校园生活」——校桥让资源流转更高效", {
    x: 0.5, y: 6.4, w: 12.3, h: 0.6, margin: 0,
    fontSize: 14, bold: true, color: C.white, fontFace: FONT_BODY, align: "center", valign: "middle"
  });

  // ============ 第 6 页：分隔页 02 ============
  let s6 = pres.addSlide();
  s6.background = { color: C.midnight };
  s6.addShape(pres.shapes.OVAL, {
    x: 10.5, y: -1, w: 4, h: 4,
    fill: { color: C.deep, transparency: 60 }, line: { type: "none" }
  });
  s6.addShape(pres.shapes.OVAL, {
    x: -1, y: 5, w: 3, h: 3,
    fill: { color: C.teal, transparency: 70 }, line: { type: "none" }
  });
  s6.addText("PART 02", {
    x: 0.5, y: 2.5, w: 12, h: 0.5, margin: 0,
    fontSize: 18, color: C.accent, fontFace: "Consolas", charSpacing: 6
  });
  s6.addText("功能描述", {
    x: 0.5, y: 3.0, w: 12, h: 1.0, margin: 0,
    fontSize: 54, bold: true, color: C.white, fontFace: FONT_HEADER
  });
  s6.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.1, w: 1.0, h: 0.06,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s6.addText("Core Functions Overview", {
    x: 0.5, y: 4.3, w: 12, h: 0.4, margin: 0,
    fontSize: 20, italic: true, color: C.lightGray, fontFace: "Consolas"
  });

  // ============ 第 7 页：四大核心功能概览 ============
  let s7 = pres.addSlide();
  s7.background = { color: C.white };

  s7.addText("四大核心功能", {
    x: 0.5, y: 0.4, w: 8, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s7.addText("学习资料 / 校园论坛 / 竞赛组队 / 二手教材", {
    x: 0.5, y: 1.05, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  // 大图：系统架构
  const funcs = [
    { icon: FaBook, name: "学习资料", count: "7+", subtitle: "功能点", color: C.deep, desc: "上传 · 检索 · 预览 · 下载 · 评价" },
    { icon: FaComments, name: "校园论坛", count: "5", subtitle: "分区", color: C.teal, desc: "发帖 · 回复 · 点赞 · 收藏 · 搜索" },
    { icon: FaUsers, name: "竞赛组队", count: "6+", subtitle: "功能点", color: C.success, desc: "招募 · 申请 · 审核 · 队伍管理" },
    { icon: FaExchangeAlt, name: "二手教材", count: "4", subtitle: "状态", color: C.accent, desc: "发布 · 搜索 · 私信 · 交易跟踪" }
  ];

  for (let i = 0; i < funcs.length; i++) {
    const f = funcs[i];
    const x = 0.5 + i * 3.2;
    // 主色块
    s7.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.9, h: 4.3,
      fill: { color: C.white }, line: { color: f.color, width: 2 },
      shadow: makeShadow()
    });
    // 顶部色条
    s7.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.9, h: 1.5,
      fill: { color: f.color }, line: { type: "none" }
    });
    // 圆形装饰
    s7.addShape(pres.shapes.OVAL, {
      x: x + 1.0, y: 2.2, w: 0.9, h: 0.9,
      fill: { color: C.white, transparency: 15 }, line: { type: "none" }
    });
    // 图标
    const iconData = await icon(f.icon, "#" + f.color, 256);
    s7.addImage({ data: iconData, x: x + 1.1, y: 2.3, w: 0.7, h: 0.7 });
    // 名称
    s7.addText(f.name, {
      x: x, y: 3.55, w: 2.9, h: 0.5, margin: 0,
      fontSize: 22, bold: true, color: C.midnight, fontFace: FONT_HEADER, align: "center"
    });
    // 数字
    s7.addText([
      { text: f.count, options: { fontSize: 36, bold: true, color: f.color, fontFace: "Consolas" } },
      { text: " " + f.subtitle, options: { fontSize: 12, color: C.textLight, fontFace: FONT_BODY } }
    ], { x: x, y: 4.2, w: 2.9, h: 0.7, margin: 0, align: "center" });
    // 分隔
    s7.addShape(pres.shapes.RECTANGLE, {
      x: x + 1.1, y: 4.95, w: 0.7, h: 0.03,
      fill: { color: f.color }, line: { type: "none" }
    });
    // 描述
    s7.addText(f.desc, {
      x: x + 0.1, y: 5.1, w: 2.7, h: 1.0, margin: 0,
      fontSize: 12, color: C.textLight, fontFace: FONT_BODY, align: "center"
    });
  }

  // 底部
  s7.addText("+ 用户认证 · RBAC权限 · 消息通知 · 后台管理 四大支撑能力", {
    x: 0.5, y: 6.45, w: 12.3, h: 0.4, margin: 0,
    fontSize: 12, italic: true, color: C.deep, fontFace: FONT_BODY, align: "center"
  });

  // ============ 第 8 页：学习资料模块 ============
  let s8 = pres.addSlide();
  s8.background = { color: C.white };

  s8.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.3, h: 7.5,
    fill: { color: C.deep }, line: { type: "none" }
  });
  s8.addText("01", {
    x: 0.6, y: 0.4, w: 1.5, h: 0.4, margin: 0,
    fontSize: 14, color: C.deep, fontFace: "Consolas", bold: true
  });
  s8.addText("学习资料共享模块", {
    x: 0.6, y: 0.8, w: 12, h: 0.6, margin: 0,
    fontSize: 28, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s8.addText("集中存储 · 分类浏览 · 在线预览 · 互动评价", {
    x: 0.6, y: 1.45, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });

  const matFeatures = [
    { icon: FaUpload, title: "资料上传", desc: "支持 PDF/Word/PPT/图片 等多种格式" },
    { icon: FaSearch, title: "关键词检索", desc: "标题、标签、作者多维精准搜索" },
    { icon: FaEye, title: "在线预览", desc: "图片 PDF 直接在浏览器内查看" },
    { icon: FaDownload, title: "一键下载", desc: "下载量自动统计，热门资源推荐" },
    { icon: FaStar, title: "五星评价", desc: "1-5星评分 + 文字评论，质量可追溯" },
    { icon: FaBookmark, title: "我的收藏", desc: "重要资料一键收藏，私人资源库" }
  ];

  for (let i = 0; i < matFeatures.length; i++) {
    const f = matFeatures[i];
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * 4.2, y = 2.0 + row * 2.4;
    s8.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 3.9, h: 2.1,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    const iconData = await icon(f.icon, "#" + C.deep, 256);
    s8.addImage({ data: iconData, x: x + 0.3, y: y + 0.4, w: 0.7, h: 0.7 });
    s8.addText(f.title, {
      x: x + 1.2, y: y + 0.4, w: 2.5, h: 0.4, margin: 0,
      fontSize: 16, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    s8.addText(f.desc, {
      x: x + 1.2, y: y + 0.9, w: 2.5, h: 1.0, margin: 0,
      fontSize: 11, color: C.textLight, fontFace: FONT_BODY, valign: "top"
    });
  }

  // ============ 第 9 页：校园论坛模块 ============
  let s9 = pres.addSlide();
  s9.background = { color: C.white };

  s9.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.3, h: 7.5,
    fill: { color: C.teal }, line: { type: "none" }
  });
  s9.addText("02", {
    x: 0.6, y: 0.4, w: 1.5, h: 0.4, margin: 0,
    fontSize: 14, color: C.teal, fontFace: "Consolas", bold: true
  });
  s9.addText("校园交流论坛模块", {
    x: 0.6, y: 0.8, w: 12, h: 0.6, margin: 0,
    fontSize: 28, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s9.addText("分区讨论 · 沉淀知识 · 互动活跃", {
    x: 0.6, y: 1.45, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });

  // 左侧：分区
  s9.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 2.0, w: 6.0, h: 4.5,
    fill: { color: C.light }, line: { type: "none" },
    shadow: makeShadow()
  });
  s9.addText("五大讨论分区", {
    x: 0.8, y: 2.1, w: 5.6, h: 0.4, margin: 0,
    fontSize: 18, bold: true, color: C.teal, fontFace: FONT_HEADER
  });
  const categories = [
    "📚 学业答疑 - 课程作业、考研考公",
    "💼 实习招聘 - 校招信息、内推分享",
    "🏠 校园生活 - 食堂宿舍、失物招领",
    "🎯 项目合作 - 课程设计、创业组队",
    "💬 杂谈灌水 - 自由交流、树洞倾诉"
  ];
  s9.addText(categories.map((c, i) => ({
    text: c, options: { breakLine: i < categories.length - 1, fontSize: 13, color: C.text }
  })), {
    x: 0.8, y: 2.6, w: 5.6, h: 3.7, fontFace: FONT_BODY, paraSpaceAfter: 8
  });

  // 右侧：互动功能
  s9.addShape(pres.shapes.RECTANGLE, {
    x: 6.9, y: 2.0, w: 6.0, h: 4.5,
    fill: { color: C.light }, line: { type: "none" },
    shadow: makeShadow()
  });
  s9.addText("互动能力", {
    x: 7.1, y: 2.1, w: 5.6, h: 0.4, margin: 0,
    fontSize: 18, bold: true, color: C.teal, fontFace: FONT_HEADER
  });

  const forumFeats = [
    { icon: FaFileAlt, t: "发帖/编辑/删除", d: "支持富文本" },
    { icon: FaCommentDots, t: "树状回复", d: "楼中楼结构" },
    { icon: FaThumbsUp, t: "点赞/收藏", d: "一键操作" },
    { icon: FaSearch, t: "全文搜索", d: "跨分区检索" }
  ];

  for (let i = 0; i < forumFeats.length; i++) {
    const f = forumFeats[i];
    const x = 7.1 + (i % 2) * 2.9, y = 2.6 + Math.floor(i / 2) * 1.9;
    const iconData = await icon(f.icon, "#" + C.teal, 256);
    s9.addImage({ data: iconData, x: x, y: y, w: 0.5, h: 0.5 });
    s9.addText(f.t, {
      x: x + 0.6, y: y, w: 2.2, h: 0.4, margin: 0,
      fontSize: 14, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    s9.addText(f.d, {
      x: x + 0.6, y: y + 0.45, w: 2.2, h: 0.3, margin: 0,
      fontSize: 11, color: C.textLight, fontFace: FONT_BODY
    });
  }

  // ============ 第 10 页：竞赛组队模块 ============
  let s10 = pres.addSlide();
  s10.background = { color: C.white };

  s10.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.3, h: 7.5,
    fill: { color: C.success }, line: { type: "none" }
  });
  s10.addText("03", {
    x: 0.6, y: 0.4, w: 1.5, h: 0.4, margin: 0,
    fontSize: 14, color: C.success, fontFace: "Consolas", bold: true
  });
  s10.addText("竞赛组队模块", {
    x: 0.6, y: 0.8, w: 12, h: 0.6, margin: 0,
    fontSize: 28, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s10.addText("从发布招募到队伍管理的全流程", {
    x: 0.6, y: 1.45, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });

  // 流程时间线
  const flowSteps = [
    { icon: FaBullhorn, t: "发布招募", d: "竞赛信息 + 角色需求" },
    { icon: FaUserPlus, t: "队员申请", d: "技能 + 自我介绍" },
    { icon: FaUserCheck, t: "队长审核", d: "通过/拒绝操作" },
    { icon: FaUsers, t: "队伍组建", d: "成员信息聚合" },
    { icon: FaHandshake, t: "协同参赛", d: "私信沟通 + 资料共享" }
  ];

  const stepW = 2.4, startX = 0.6;
  for (let i = 0; i < flowSteps.length; i++) {
    const f = flowSteps[i];
    const x = startX + i * (stepW + 0.1);
    // 卡片
    s10.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 2.2, w: stepW, h: 3.5,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    // 顶部圆形
    s10.addShape(pres.shapes.OVAL, {
      x: x + (stepW - 1.0) / 2, y: 2.4, w: 1.0, h: 1.0,
      fill: { color: C.success }, line: { type: "none" }
    });
    const iconData = await icon(f.icon, "#FFFFFF", 256);
    s10.addImage({ data: iconData, x: x + (stepW - 0.5) / 2, y: 2.65, w: 0.5, h: 0.5 });
    // 步骤编号
    s10.addText("STEP " + (i + 1), {
      x: x, y: 3.6, w: stepW, h: 0.3, margin: 0,
      fontSize: 10, color: C.success, fontFace: "Consolas", align: "center", bold: true
    });
    // 标题
    s10.addText(f.t, {
      x: x, y: 3.95, w: stepW, h: 0.4, margin: 0,
      fontSize: 16, bold: true, color: C.midnight, fontFace: FONT_HEADER, align: "center"
    });
    // 描述
    s10.addText(f.d, {
      x: x + 0.2, y: 4.45, w: stepW - 0.4, h: 1.0, margin: 0,
      fontSize: 11, color: C.textLight, fontFace: FONT_BODY, align: "center"
    });
    // 箭头
    if (i < flowSteps.length - 1) {
      s10.addShape(pres.shapes.RIGHT_TRIANGLE, {
        x: x + stepW - 0.1, y: 3.8, w: 0.3, h: 0.3,
        fill: { color: C.success }, line: { type: "none" }, rotate: 90
      });
    }
  }

  // 底部特点
  s10.addText("亮点：支持跨院系招募、状态实时跟踪、自动消息通知", {
    x: 0.6, y: 6.3, w: 12.3, h: 0.4, margin: 0,
    fontSize: 13, italic: true, color: C.success, fontFace: FONT_BODY, align: "center"
  });

  // ============ 第 11 页：二手教材模块 ============
  let s11 = pres.addSlide();
  s11.background = { color: C.white };

  s11.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.3, h: 7.5,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s11.addText("04", {
    x: 0.6, y: 0.4, w: 1.5, h: 0.4, margin: 0,
    fontSize: 14, color: C.accent, fontFace: "Consolas", bold: true
  });
  s11.addText("二手教材交换模块", {
    x: 0.6, y: 0.8, w: 12, h: 0.6, margin: 0,
    fontSize: 28, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s11.addText("闲置流转 · 绿色校园 · 交易透明", {
    x: 0.6, y: 1.45, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });

  // 左侧：状态机
  s11.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 2.0, w: 7.0, h: 4.6,
    fill: { color: C.light }, line: { type: "none" },
    shadow: makeShadow()
  });
  s11.addText("交易状态机", {
    x: 0.8, y: 2.1, w: 6.6, h: 0.4, margin: 0,
    fontSize: 18, bold: true, color: C.accent, fontFace: FONT_HEADER
  });

  const states = [
    { icon: FaCheckCircle, name: "在售", color: C.success, desc: "买家可申请" },
    { icon: FaClock, name: "已预订", color: C.accent, desc: "已有人锁定" },
    { icon: FaSyncAlt, name: "交易中", color: C.teal, desc: "沟通确认中" },
    { icon: FaCheck, name: "已完成", color: C.deep, desc: "交易归档" }
  ];

  for (let i = 0; i < states.length; i++) {
    const s = states[i];
    const x = 0.8 + i * 1.65, y = 2.8;
    s11.addShape(pres.shapes.OVAL, {
      x: x + 0.4, y: y, w: 0.8, h: 0.8,
      fill: { color: s.color }, line: { type: "none" }
    });
    const iconData = await icon(s.icon, "#FFFFFF", 256);
    s11.addImage({ data: iconData, x: x + 0.55, y: y + 0.15, w: 0.5, h: 0.5 });
    s11.addText(s.name, {
      x: x, y: y + 0.95, w: 1.6, h: 0.4, margin: 0,
      fontSize: 14, bold: true, color: C.midnight, fontFace: FONT_HEADER, align: "center"
    });
    s11.addText(s.desc, {
      x: x, y: y + 1.35, w: 1.6, h: 0.3, margin: 0,
      fontSize: 10, color: C.textLight, fontFace: FONT_BODY, align: "center"
    });
    if (i < states.length - 1) {
      s11.addShape(pres.shapes.RECTANGLE, {
        x: x + 1.45, y: y + 0.38, w: 0.3, h: 0.04,
        fill: { color: C.gray }, line: { type: "none" }
      });
    }
  }

  // 左侧底部：核心特性
  s11.addText("核心特性", {
    x: 0.8, y: 5.1, w: 6.6, h: 0.3, margin: 0,
    fontSize: 14, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s11.addText([
    { text: "●  书籍图片、ISBN、新旧程度等多维信息", options: { breakLine: true, fontSize: 12, color: C.text } },
    { text: "●  站内私信沟通，保护双方隐私", options: { breakLine: true, fontSize: 12, color: C.text } },
    { text: "●  状态自动流转，操作日志可追溯", options: { fontSize: 12, color: C.text } }
  ], { x: 0.8, y: 5.4, w: 6.6, h: 1.1, fontFace: FONT_BODY, paraSpaceAfter: 3 });

  // 右侧：核心功能
  s11.addShape(pres.shapes.RECTANGLE, {
    x: 7.9, y: 2.0, w: 5.0, h: 4.6,
    fill: { color: C.accent }, line: { type: "none" },
    shadow: makeShadow()
  });
  s11.addText("完整闭环", {
    x: 8.1, y: 2.1, w: 4.6, h: 0.4, margin: 0,
    fontSize: 18, bold: true, color: C.white, fontFace: FONT_HEADER
  });

  const tbFeats = [
    { icon: FaUpload, t: "发布闲置" },
    { icon: FaSearch, t: "按书名/作者搜索" },
    { icon: FaCommentDots, t: "站内私信沟通" },
    { icon: FaShoppingCart, t: "状态实时跟踪" }
  ];

  for (let i = 0; i < tbFeats.length; i++) {
    const f = tbFeats[i];
    const y = 2.7 + i * 0.85;
    const iconData = await icon(f.icon, "#FFFFFF", 256);
    s11.addImage({ data: iconData, x: 8.1, y: y, w: 0.5, h: 0.5 });
    s11.addText(f.t, {
      x: 8.7, y: y + 0.05, w: 4.0, h: 0.4, margin: 0,
      fontSize: 15, color: C.white, fontFace: FONT_HEADER
    });
  }

  // ============ 第 12 页：支撑能力 ============
  let s12 = pres.addSlide();
  s12.background = { color: C.white };

  s12.addText("支撑能力", {
    x: 0.5, y: 0.4, w: 8, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s12.addText("贯穿全局的四大支撑能力", {
    x: 0.5, y: 1.05, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s12.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const supports = [
    { icon: FaUserShield, t: "用户认证", d: "注册登录、密码加密、会话管理", color: C.deep, sub: "Flask-Login" },
    { icon: FaUserCircle, t: "RBAC 权限", d: "普通用户/管理员双角色", color: C.teal, sub: "Decorator" },
    { icon: FaBell, t: "消息通知", d: "系统通知 + 未读红点 + 实时提醒", color: C.accent, sub: "WebSocket 可扩展" },
    { icon: FaCog, t: "后台管理", d: "用户/资料/帖子/教材/分区治理", color: C.success, sub: "Admin Dashboard" }
  ];

  for (let i = 0; i < supports.length; i++) {
    const s = supports[i];
    const x = 0.5 + i * 3.2;
    s12.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.9, h: 4.3,
      fill: { color: C.white }, line: { color: s.color, width: 2 },
      shadow: makeShadow()
    });
    s12.addShape(pres.shapes.OVAL, {
      x: x + 1.05, y: 2.2, w: 0.8, h: 0.8,
      fill: { color: s.color }, line: { type: "none" }
    });
    const iconData = await icon(s.icon, "#FFFFFF", 256);
    s12.addImage({ data: iconData, x: x + 1.2, y: 2.35, w: 0.5, h: 0.5 });
    s12.addText(s.t, {
      x: x, y: 3.2, w: 2.9, h: 0.4, margin: 0,
      fontSize: 18, bold: true, color: C.midnight, fontFace: FONT_HEADER, align: "center"
    });
    s12.addText(s.d, {
      x: x + 0.2, y: 3.7, w: 2.5, h: 1.0, margin: 0,
      fontSize: 12, color: C.textLight, fontFace: FONT_BODY, align: "center"
    });
    // 技术标签
    s12.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.6, y: 5.2, w: 1.7, h: 0.4,
      fill: { color: s.color, transparency: 80 }, line: { type: "none" }
    });
    s12.addText(s.sub, {
      x: x + 0.6, y: 5.2, w: 1.7, h: 0.4, margin: 0,
      fontSize: 10, color: s.color, fontFace: "Consolas", align: "center", valign: "middle", bold: true
    });
  }

  // ============ 第 13 页：分隔页 03 ============
  let s13 = pres.addSlide();
  s13.background = { color: C.midnight };
  s13.addShape(pres.shapes.OVAL, {
    x: 10.5, y: -1, w: 4, h: 4,
    fill: { color: C.deep, transparency: 60 }, line: { type: "none" }
  });
  s13.addShape(pres.shapes.OVAL, {
    x: -1, y: 5, w: 3, h: 3,
    fill: { color: C.teal, transparency: 70 }, line: { type: "none" }
  });
  s13.addText("PART 03", {
    x: 0.5, y: 2.5, w: 12, h: 0.5, margin: 0,
    fontSize: 18, color: C.accent, fontFace: "Consolas", charSpacing: 6
  });
  s13.addText("可行性分析", {
    x: 0.5, y: 3.0, w: 12, h: 1.0, margin: 0,
    fontSize: 54, bold: true, color: C.white, fontFace: FONT_HEADER
  });
  s13.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.1, w: 1.0, h: 0.06,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s13.addText("Feasibility Analysis", {
    x: 0.5, y: 4.3, w: 12, h: 0.4, margin: 0,
    fontSize: 20, italic: true, color: C.lightGray, fontFace: "Consolas"
  });

  // ============ 第 14 页：技术可行性 ============
  let s14 = pres.addSlide();
  s14.background = { color: C.white };

  s14.addText("技术可行性", {
    x: 0.5, y: 0.4, w: 8, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s14.addText("成熟开源技术栈 · 学习曲线友好", {
    x: 0.5, y: 1.05, w: 8, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s14.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  // 左侧：技术栈
  s14.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.9, w: 6.0, h: 4.6,
    fill: { color: C.light }, line: { type: "none" },
    shadow: makeShadow()
  });
  s14.addText("技术选型", {
    x: 0.7, y: 2.0, w: 5.6, h: 0.4, margin: 0,
    fontSize: 18, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });

  const techStack = [
    { icon: FaPython, t: "Python 3.10+", d: "开发语言", color: C.deep },
    { icon: FaFlask, t: "Flask 3.0", d: "Web 框架 + Jinja2 模板", color: C.teal },
    { icon: FaDatabase, t: "MySQL 8.0", d: "关系型数据库", color: C.accent },
    { icon: FaServer, t: "Flask-SQLAlchemy", d: "ORM 框架", color: C.success },
    { icon: FaCode, t: "原生 JavaScript", d: "前端交互（无框架）", color: C.coral },
    { icon: FaCloud, t: "腾讯云 COS", d: "云存储（可降级本地）", color: C.deep }
  ];

  for (let i = 0; i < techStack.length; i++) {
    const t = techStack[i];
    const y = 2.5 + i * 0.65;
    const iconData = await icon(t.icon, "#" + t.color, 256);
    s14.addImage({ data: iconData, x: 0.8, y: y, w: 0.4, h: 0.4 });
    s14.addText(t.t, {
      x: 1.3, y: y, w: 2.5, h: 0.4, margin: 0,
      fontSize: 14, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    s14.addText(t.d, {
      x: 3.8, y: y + 0.05, w: 2.6, h: 0.4, margin: 0,
      fontSize: 11, color: C.textLight, fontFace: FONT_BODY
    });
  }

  // 右侧：可行性优势
  s14.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 1.9, w: 6.1, h: 4.6,
    fill: { color: C.midnight }, line: { type: "none" },
    shadow: makeShadow()
  });
  s14.addText("可行性优势", {
    x: 7.0, y: 2.0, w: 5.7, h: 0.4, margin: 0,
    fontSize: 18, bold: true, color: C.white, fontFace: FONT_HEADER
  });

  const advItems = [
    { t: "成熟稳定", d: "Flask + MySQL 均为工业级主流方案" },
    { t: "文档丰富", d: "官方文档 + 中文社区资源充足" },
    { t: "团队熟悉", d: "团队成员均具备 Python Web 基础" },
    { t: "轻量部署", d: "单进程运行，本地演示零成本" },
    { t: "可扩展性", d: "模块化设计，云存储接入预留接口" }
  ];

  for (let i = 0; i < advItems.length; i++) {
    const a = advItems[i];
    const y = 2.6 + i * 0.75;
    s14.addShape(pres.shapes.OVAL, {
      x: 7.0, y: y + 0.05, w: 0.4, h: 0.4,
      fill: { color: C.accent }, line: { type: "none" }
    });
    s14.addText((i + 1).toString(), {
      x: 7.0, y: y + 0.05, w: 0.4, h: 0.4, margin: 0,
      fontSize: 14, bold: true, color: C.white, fontFace: "Consolas", align: "center", valign: "middle"
    });
    s14.addText(a.t, {
      x: 7.55, y: y, w: 5.0, h: 0.35, margin: 0,
      fontSize: 15, bold: true, color: C.white, fontFace: FONT_HEADER
    });
    s14.addText(a.d, {
      x: 7.55, y: y + 0.35, w: 5.0, h: 0.3, margin: 0,
      fontSize: 11, color: C.lightGray, fontFace: FONT_BODY
    });
  }

  // ============ 第 15 页：经济与社会可行性 ============
  let s15 = pres.addSlide();
  s15.background = { color: C.white };

  s15.addText("经济与社会可行性", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s15.addText("低成本开发 · 强用户需求 · 校方支持", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s15.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  // 三大对比卡片
  const feas = [
    { icon: FaBriefcase, t: "经济可行性", color: C.deep, points: [
      "技术栈全部开源免费，零软件采购成本",
      "本地部署无需服务器，演示零运营费用",
      "上线后可对接云服务，按需付费成本可控"
    ] },
    { icon: FaUniversity, t: "社会可行性", color: C.teal, points: [
      "校园资源浪费是普遍痛点，用户需求真实",
      "响应绿色校园、共享经济国家政策导向",
      "提升学生数字素养与协作能力"
    ] },
    { icon: FaChartLine, t: "运营可行性", color: C.success, points: [
      "目标用户群体明确（在校师生）",
      "可由学校信息中心/学生会推广",
      "低运营门槛，无须专职运维人员"
    ] }
  ];

  for (let i = 0; i < feas.length; i++) {
    const f = feas[i];
    const x = 0.5 + i * 4.2;
    s15.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 3.9, h: 4.6,
      fill: { color: C.white }, line: { color: f.color, width: 2 },
      shadow: makeShadow()
    });
    s15.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 3.9, h: 0.9,
      fill: { color: f.color }, line: { type: "none" }
    });
    const iconData = await icon(f.icon, "#FFFFFF", 256);
    s15.addImage({ data: iconData, x: x + 0.3, y: 2.1, w: 0.5, h: 0.5 });
    s15.addText(f.t, {
      x: x + 1.0, y: 2.1, w: 2.7, h: 0.5, margin: 0,
      fontSize: 18, bold: true, color: C.white, fontFace: FONT_HEADER, valign: "middle"
    });
    const points = f.points.map((p, j) => ({
      text: p, options: { bullet: { code: "25A0" }, breakLine: j < f.points.length - 1, fontSize: 12, color: C.text, paraSpaceAfter: 8 }
    }));
    s15.addText(points, {
      x: x + 0.3, y: 3.0, w: 3.4, h: 3.3, fontFace: FONT_BODY, valign: "top"
    });
  }

  // ============ 第 16 页：风险与对策 ============
  let s16 = pres.addSlide();
  s16.background = { color: C.white };

  s16.addText("风险与对策", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s16.addText("识别风险，未雨绸缪", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s16.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const risks = [
    { r: "并发性能瓶颈", c: "采用 Flask 多线程模式，数据库连接池；接口设计简洁，演示场景压力可控", color: C.deep },
    { r: "文件存储容量", c: "默认本地降级，限制单文件 16MB；后续可平滑迁移到腾讯云 COS", color: C.teal },
    { r: "内容审核风险", c: "管理员后台可对违规资料/帖子/教材下架，建立举报闭环", color: C.accent },
    { r: "用户隐私安全", c: "密码 bcrypt 加密，会话 token 化管理，私信不暴露联系方式", color: C.success }
  ];

  for (let i = 0; i < risks.length; i++) {
    const r = risks[i];
    const y = 1.9 + i * 1.15;
    s16.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 12.4, h: 1.0,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    s16.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 0.15, h: 1.0,
      fill: { color: r.color }, line: { type: "none" }
    });
    s16.addText("⚠", {
      x: 0.8, y: y + 0.15, w: 0.5, h: 0.5, margin: 0,
      fontSize: 28, color: r.color, fontFace: "Arial", valign: "middle"
    });
    s16.addText(r.r, {
      x: 1.4, y: y + 0.1, w: 3.0, h: 0.4, margin: 0,
      fontSize: 16, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    s16.addText("对策：" + r.c, {
      x: 1.4, y: y + 0.5, w: 11.0, h: 0.45, margin: 0,
      fontSize: 12, color: C.textLight, fontFace: FONT_BODY
    });
  }

  // ============ 第 17 页：分隔页 04 ============
  let s17 = pres.addSlide();
  s17.background = { color: C.midnight };
  s17.addShape(pres.shapes.OVAL, {
    x: 10.5, y: -1, w: 4, h: 4,
    fill: { color: C.deep, transparency: 60 }, line: { type: "none" }
  });
  s17.addShape(pres.shapes.OVAL, {
    x: -1, y: 5, w: 3, h: 3,
    fill: { color: C.teal, transparency: 70 }, line: { type: "none" }
  });
  s17.addText("PART 04", {
    x: 0.5, y: 2.5, w: 12, h: 0.5, margin: 0,
    fontSize: 18, color: C.accent, fontFace: "Consolas", charSpacing: 6
  });
  s17.addText("技术路线与进度安排", {
    x: 0.5, y: 3.0, w: 12, h: 1.0, margin: 0,
    fontSize: 48, bold: true, color: C.white, fontFace: FONT_HEADER
  });
  s17.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.1, w: 1.0, h: 0.06,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s17.addText("Technical Route & Schedule", {
    x: 0.5, y: 4.3, w: 12, h: 0.4, margin: 0,
    fontSize: 20, italic: true, color: C.lightGray, fontFace: "Consolas"
  });

  // ============ 第 18 页：系统架构图 ============
  let s18 = pres.addSlide();
  s18.background = { color: C.white };

  s18.addText("系统架构", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s18.addText("经典三层架构 · 前后端一体化部署", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s18.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  // 架构分层
  const layers = [
    { t: "表现层", sub: "Jinja2 模板 + 原生 JavaScript + Tailwind CSS", color: C.deep, items: ["base.html", "templates/", "static/"] },
    { t: "业务层", sub: "Flask 蓝图路由 + 权限装饰器 + 表单校验", color: C.teal, items: ["routes_*.py", "decorators.py", "forms.py"] },
    { t: "数据层", sub: "SQLAlchemy ORM + MySQL 8.0 + 云存储抽象", color: C.success, items: ["models.py", "db_init.sql", "storage.py"] }
  ];

  for (let i = 0; i < layers.length; i++) {
    const l = layers[i];
    const y = 1.9 + i * 1.55;
    s18.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 12.4, h: 1.3,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    s18.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 3.0, h: 1.3,
      fill: { color: l.color }, line: { type: "none" }
    });
    s18.addText(l.t, {
      x: 0.5, y: y + 0.2, w: 3.0, h: 0.4, margin: 0,
      fontSize: 20, bold: true, color: C.white, fontFace: FONT_HEADER, align: "center"
    });
    s18.addText("Layer " + (i + 1), {
      x: 0.5, y: y + 0.65, w: 3.0, h: 0.3, margin: 0,
      fontSize: 11, color: C.white, fontFace: "Consolas", align: "center", italic: true
    });
    s18.addText(l.sub, {
      x: 3.7, y: y + 0.2, w: 9.0, h: 0.4, margin: 0,
      fontSize: 14, color: C.midnight, fontFace: FONT_BODY
    });
    s18.addText(l.items.map((it, j) => ({
      text: it, options: { fontSize: 11, color: C.textLight, fontFace: "Consolas" }
    })).reduce((acc, cur, j) => acc.concat(cur, { text: "    ", options: { fontSize: 11, color: C.textLight } }), []), {
      x: 3.7, y: y + 0.7, w: 9.0, h: 0.4, margin: 0
    });
  }

  // 底部：核心
  s18.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 6.5, w: 12.4, h: 0.5,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s18.addText("app.py 主入口 · 配置加载 · 蓝图注册 · 上下文处理器 · 全局钩子", {
    x: 0.5, y: 6.5, w: 12.4, h: 0.5, margin: 0,
    fontSize: 12, color: C.white, fontFace: FONT_BODY, align: "center", valign: "middle", bold: true
  });

  // ============ 第 19 页：6周进度甘特图 ============
  let s19 = pres.addSlide();
  s19.background = { color: C.white };

  s19.addText("进度安排", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s19.addText("6 周迭代开发 · 敏捷推进", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s19.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  // 甘特图
  const ganttHeaderY = 2.0;
  const ganttRowH = 0.6;
  const ganttX = 3.2;
  const ganttW = 9.5;
  const weekW = ganttW / 6;

  // 表头：周次
  for (let i = 0; i < 6; i++) {
    s19.addShape(pres.shapes.RECTANGLE, {
      x: ganttX + i * weekW, y: ganttHeaderY, w: weekW, h: 0.4,
      fill: { color: C.midnight }, line: { color: C.white, width: 1 }
    });
    s19.addText("第" + (i + 1) + "周", {
      x: ganttX + i * weekW, y: ganttHeaderY, w: weekW, h: 0.4, margin: 0,
      fontSize: 12, bold: true, color: C.white, fontFace: FONT_BODY, align: "center", valign: "middle"
    });
  }

  // 任务行
  const tasks = [
    { name: "需求分析", weeks: [0, 1], color: C.deep, status: "完成" },
    { name: "系统设计", weeks: [0, 2], color: C.teal, status: "完成" },
    { name: "项目骨架", weeks: [1, 2], color: C.deep, status: "完成" },
    { name: "认证 RBAC", weeks: [1, 2], color: C.teal, status: "完成" },
    { name: "学习资料", weeks: [2, 4], color: C.success, status: "完成" },
    { name: "校园论坛", weeks: [2, 4], color: C.accent, status: "完成" },
    { name: "竞赛组队", weeks: [3, 4], color: C.coral, status: "完成" },
    { name: "二手教材", weeks: [3, 5], color: C.deep, status: "完成" },
    { name: "消息通知", weeks: [4, 5], color: C.teal, status: "完成" },
    { name: "后台管理", weeks: [4, 5], color: C.success, status: "完成" },
    { name: "测试部署", weeks: [4, 6], color: C.accent, status: "进行中" },
    { name: "优化文档", weeks: [5, 6], color: C.coral, status: "计划中" }
  ];

  for (let i = 0; i < tasks.length; i++) {
    const t = tasks[i];
    const y = ganttHeaderY + 0.4 + i * ganttRowH;
    // 行背景
    s19.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 12.4, h: ganttRowH,
      fill: { color: i % 2 === 0 ? C.white : C.light }, line: { type: "none" }
    });
    // 任务名
    s19.addText(t.name, {
      x: 0.6, y: y, w: 2.5, h: ganttRowH, margin: 0,
      fontSize: 11, color: C.midnight, fontFace: FONT_BODY, valign: "middle"
    });
    // 进度条
    const startX = ganttX + t.weeks[0] * weekW + 0.05;
    const barW = (t.weeks[1] - t.weeks[0] + 1) * weekW - 0.1;
    s19.addShape(pres.shapes.RECTANGLE, {
      x: startX, y: y + 0.15, w: barW, h: 0.3,
      fill: { color: t.color }, line: { type: "none" }
    });
    // 状态标签
    s19.addText(t.status, {
      x: startX, y: y + 0.15, w: barW, h: 0.3, margin: 0,
      fontSize: 9, color: C.white, fontFace: FONT_BODY, align: "center", valign: "middle", bold: true
    });
  }

  // ============ 第 20 页：团队分工 ============
  let s20 = pres.addSlide();
  s20.background = { color: C.white };

  s20.addText("团队分工", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s20.addText("5 人敏捷小组 · 角色互补", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s20.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const roles = [
    { icon: FaRocket, name: "项目经理", responsibilities: ["整体进度把控", "需求拆解与排期", "对外汇报与协调"], color: C.deep },
    { icon: FaBook, name: "需求分析", responsibilities: ["需求调研", "需求规格说明书", "用户故事编写"], color: C.teal },
    { icon: FaCode, name: "前端开发", responsibilities: ["页面原型设计", "模板开发", "CSS/JS 交互"], color: C.success },
    { icon: FaServer, name: "后端开发", responsibilities: ["数据库设计", "接口开发", "业务逻辑实现"], color: C.accent },
    { icon: FaCheckCircle, name: "测试部署", responsibilities: ["功能/性能测试", "部署文档", "用户手册"], color: C.coral }
  ];

  for (let i = 0; i < roles.length; i++) {
    const r = roles[i];
    const x = 0.5 + i * 2.5;
    s20.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.3, h: 4.5,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    s20.addShape(pres.shapes.OVAL, {
      x: x + 0.7, y: 2.1, w: 0.9, h: 0.9,
      fill: { color: r.color }, line: { type: "none" }
    });
    const iconData = await icon(r.icon, "#FFFFFF", 256);
    s20.addImage({ data: iconData, x: x + 0.85, y: 2.25, w: 0.6, h: 0.6 });
    s20.addText(r.name, {
      x: x, y: 3.15, w: 2.3, h: 0.4, margin: 0,
      fontSize: 16, bold: true, color: C.midnight, fontFace: FONT_HEADER, align: "center"
    });
    s20.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.8, y: 3.6, w: 0.7, h: 0.03,
      fill: { color: r.color }, line: { type: "none" }
    });
    s20.addText("职责", {
      x: x, y: 3.75, w: 2.3, h: 0.3, margin: 0,
      fontSize: 11, color: r.color, fontFace: FONT_BODY, align: "center", bold: true
    });
    s20.addText(r.responsibilities.map((rp, j) => ({
      text: "● " + rp, options: { breakLine: j < r.responsibilities.length - 1, fontSize: 11, color: C.text, paraSpaceAfter: 6 }
    })), {
      x: x + 0.2, y: 4.05, w: 2.0, h: 2.3, fontFace: FONT_BODY, valign: "top"
    });
  }

  // 底部说明
  s20.addText("注：实际成员姓名以项目结题时为准，团队采用周例会+日站会的敏捷协作模式", {
    x: 0.5, y: 6.5, w: 12.4, h: 0.4, margin: 0,
    fontSize: 10, italic: true, color: C.gray, fontFace: FONT_BODY, align: "center"
  });

  // ============ 第 21 页：分隔页 05 ============
  let s21 = pres.addSlide();
  s21.background = { color: C.midnight };
  s21.addShape(pres.shapes.OVAL, {
    x: 10.5, y: -1, w: 4, h: 4,
    fill: { color: C.deep, transparency: 60 }, line: { type: "none" }
  });
  s21.addShape(pres.shapes.OVAL, {
    x: -1, y: 5, w: 3, h: 3,
    fill: { color: C.teal, transparency: 70 }, line: { type: "none" }
  });
  s21.addText("PART 05", {
    x: 0.5, y: 2.5, w: 12, h: 0.5, margin: 0,
    fontSize: 18, color: C.accent, fontFace: "Consolas", charSpacing: 6
  });
  s21.addText("预期成果", {
    x: 0.5, y: 3.0, w: 12, h: 1.0, margin: 0,
    fontSize: 54, bold: true, color: C.white, fontFace: FONT_HEADER
  });
  s21.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.1, w: 1.0, h: 0.06,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s21.addText("Expected Outcomes", {
    x: 0.5, y: 4.3, w: 12, h: 0.4, margin: 0,
    fontSize: 20, italic: true, color: C.lightGray, fontFace: "Consolas"
  });

  // ============ 第 22 页：交付物清单 ============
  let s22 = pres.addSlide();
  s22.background = { color: C.white };

  s22.addText("交付物清单", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s22.addText("代码 + 文档 + 系统三位一体", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s22.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const deliveries = [
    {
      icon: FaCode, t: "可运行系统", color: C.deep,
      items: ["完整源代码（37条路由）", "MySQL 初始化脚本", "一键启动文档", "本地可演示系统"]
    },
    {
      icon: FaFileAlt, t: "项目文档", color: C.teal,
      items: ["立项申请书", "需求规格说明书", "系统设计文档", "数据库设计说明"]
    },
    {
      icon: FaCheckCircle, t: "测试与部署", color: C.success,
      items: ["功能测试报告", "性能测试报告", "部署运维手册", "用户使用手册"]
    },
    {
      icon: FaGraduationCap, t: "总结与展望", color: C.accent,
      items: ["项目总结报告", "开发心得体会", "后续优化方向", "二期功能规划"]
    }
  ];

  for (let i = 0; i < deliveries.length; i++) {
    const d = deliveries[i];
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.5 + col * 6.3, y = 1.9 + row * 2.4;
    s22.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 6.0, h: 2.1,
      fill: { color: C.light }, line: { type: "none" },
      shadow: makeShadow()
    });
    s22.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 0.15, h: 2.1,
      fill: { color: d.color }, line: { type: "none" }
    });
    const iconData = await icon(d.icon, "#" + d.color, 256);
    s22.addImage({ data: iconData, x: x + 0.4, y: y + 0.3, w: 0.8, h: 0.8 });
    s22.addText(d.t, {
      x: x + 1.4, y: y + 0.25, w: 4.3, h: 0.4, margin: 0,
      fontSize: 18, bold: true, color: C.midnight, fontFace: FONT_HEADER
    });
    s22.addText(d.items.map((it, j) => ({
      text: "● " + it, options: { breakLine: j < d.items.length - 1, fontSize: 11, color: C.text, paraSpaceAfter: 2 }
    })), {
      x: x + 1.4, y: y + 0.7, w: 4.4, h: 1.4, fontFace: FONT_BODY, valign: "top"
    });
  }

  // ============ 第 23 页：关键指标 ============
  let s23 = pres.addSlide();
  s23.background = { color: C.white };

  s23.addText("关键指标", {
    x: 0.5, y: 0.4, w: 12, h: 0.6, margin: 0,
    fontSize: 30, bold: true, color: C.midnight, fontFace: FONT_HEADER
  });
  s23.addText("用数据量化项目价值", {
    x: 0.5, y: 1.05, w: 12, h: 0.3, margin: 0,
    fontSize: 13, color: C.textLight, fontFace: FONT_BODY
  });
  s23.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.45, w: 0.5, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });

  const metrics = [
    { num: "37", unit: "条", label: "API 路由", color: C.deep },
    { num: "10", unit: "个", label: "数据表", color: C.teal },
    { num: "20", unit: "张", label: "页面模板", color: C.success },
    { num: "6", unit: "大", label: "功能模块", color: C.accent }
  ];

  for (let i = 0; i < metrics.length; i++) {
    const m = metrics[i];
    const x = 0.5 + i * 3.2;
    s23.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.9, w: 2.9, h: 3.5,
      fill: { color: m.color }, line: { type: "none" },
      shadow: makeShadow()
    });
    // 装饰圆
    s23.addShape(pres.shapes.OVAL, {
      x: x + 2.1, y: 2.1, w: 0.7, h: 0.7,
      fill: { color: C.white, transparency: 80 }, line: { type: "none" }
    });
    s23.addText(m.num, {
      x: x, y: 2.4, w: 2.9, h: 1.3, margin: 0,
      fontSize: 72, bold: true, color: C.white, fontFace: "Consolas", align: "center", valign: "middle"
    });
    s23.addText(m.unit, {
      x: x, y: 3.7, w: 2.9, h: 0.3, margin: 0,
      fontSize: 14, color: C.white, fontFace: FONT_BODY, align: "center"
    });
    s23.addShape(pres.shapes.RECTANGLE, {
      x: x + 1.2, y: 4.15, w: 0.5, h: 0.04,
      fill: { color: C.white }, line: { type: "none" }
    });
    s23.addText(m.label, {
      x: x, y: 4.35, w: 2.9, h: 0.5, margin: 0,
      fontSize: 16, bold: true, color: C.white, fontFace: FONT_HEADER, align: "center"
    });
  }

  // 底部说明
  s23.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.8, w: 12.4, h: 1.1,
    fill: { color: C.light }, line: { type: "none" }
  });
  s23.addText("项目价值", {
    x: 0.7, y: 5.85, w: 12, h: 0.3, margin: 0,
    fontSize: 14, bold: true, color: C.deep, fontFace: FONT_HEADER
  });
  s23.addText("覆盖校园资源流通的完整链路：内容生产（资料）→ 互动交流（论坛）→ 协作组队（竞赛）→ 价值释放（二手）→ 通知反馈（消息）→ 平台治理（后台），形成可持续运转的校园资源生态闭环。", {
    x: 0.7, y: 6.2, w: 12, h: 0.7, margin: 0,
    fontSize: 12, color: C.textLight, fontFace: FONT_BODY
  });

  // ============ 第 24 页：结语 ============
  let s24 = pres.addSlide();
  s24.background = { color: C.midnight };

  // 装饰
  s24.addShape(pres.shapes.OVAL, {
    x: -1, y: -1, w: 4, h: 4,
    fill: { color: C.deep, transparency: 60 }, line: { type: "none" }
  });
  s24.addShape(pres.shapes.OVAL, {
    x: 11, y: 5, w: 3.5, h: 3.5,
    fill: { color: C.teal, transparency: 70 }, line: { type: "none" }
  });
  s24.addShape(pres.shapes.OVAL, {
    x: 6, y: 3, w: 1.5, h: 1.5,
    fill: { color: C.accent, transparency: 80 }, line: { type: "none" }
  });

  s24.addText("THANKS", {
    x: 0.5, y: 2.0, w: 12.3, h: 0.8, margin: 0,
    fontSize: 60, bold: true, color: C.white, fontFace: "Consolas", align: "center", charSpacing: 12
  });
  s24.addShape(pres.shapes.RECTANGLE, {
    x: 6.15, y: 3.0, w: 1.0, h: 0.05,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s24.addText("感谢聆听 · 敬请指正", {
    x: 0.5, y: 3.2, w: 12.3, h: 0.5, margin: 0,
    fontSize: 24, color: C.lightGray, fontFace: FONT_HEADER, align: "center", charSpacing: 6
  });

  s24.addText("校桥 CampusBridge", {
    x: 0.5, y: 4.5, w: 12.3, h: 0.4, margin: 0,
    fontSize: 16, color: C.white, fontFace: FONT_HEADER, align: "center"
  });
  s24.addText("Connecting Knowledge, Sharing Value", {
    x: 0.5, y: 4.95, w: 12.3, h: 0.3, margin: 0,
    fontSize: 12, italic: true, color: C.accent, fontFace: "Consolas", align: "center"
  });

  // 底部信息
  s24.addShape(pres.shapes.RECTANGLE, {
    x: 4.0, y: 6.3, w: 5.3, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" }
  });
  s24.addText("校桥项目组 · 2026.07", {
    x: 0.5, y: 6.5, w: 12.3, h: 0.4, margin: 0,
    fontSize: 13, color: C.gray, fontFace: FONT_BODY, align: "center"
  });

  // 输出
  await pres.writeFile({ fileName: "C:/工作/项目/校桥CampusBridge_开题汇报.pptx" });
  console.log("✅ PPT 已生成: 校桥CampusBridge_开题汇报.pptx");
  console.log("   共 24 页，涵盖 5 大汇报主题");
}

main().catch(err => {
  console.error("生成失败:", err);
  process.exit(1);
});
