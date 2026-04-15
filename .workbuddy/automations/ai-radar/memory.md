# AI Radar 自动化执行记忆

## 2026-04-14 (周一) 执行记录
- **状态**: ✅ 完成（有限制）
- **arXiv API**: 被 429 严重限流，改用 web fetch + 手动 PDF 验证
- **数据更新**: 343 篇论文 (+1 PhysInOne), 63 校企合作, 12 港校合作
- **新增论文**: PhysInOne (PolyU × Meta, CVPR2026) 加入 meta 公司
- **港校论文**: 发现 4 篇 (InsEdit HKUST+CityU, SATO HKU, AniGen HKU+CUHK, PhysInOne PolyU+Meta)
- **人才库**: 960 → 968 (+8人, 含4位港校教授+4位博士生), 港校人才 34→42
- **新增教授**: 陈启峰(HKUST), Taku Komura(HKU), 戚晓娟(HKU), 杨波(PolyU)
- **新增学生**: 徐瑞(HKU, SIGGRAPH2023最佳论文!), 黄一华(HKU), 饶哲凡(HKUST), 何轩华(HKUST)
- **同步**: Lighthouse API ✅, git push ✅
- **修复**: scan-arxiv.py 增加429重试逻辑(max_retries=3)和更长间隔(15s)
- **注意**: 周末(4/12-13)提交量少; DeepXiv增强因API限流暂跳过
