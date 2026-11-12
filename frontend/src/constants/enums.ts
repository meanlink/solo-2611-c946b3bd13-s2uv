export const ROLES = { admin: "数据管理员", analyst: "分析员", reviewer: "业务复核员" } as const;
export const STATUS_LABELS: Record<string,string> = { draft:"草稿", ready:"就绪", running:"运行中", completed:"已完成", failed:"失败" };
export const REVIEW_STATUS_LABELS: Record<string,string> = {
  pending: "待追查",
  false_positive: "误报",
  under_investigation: "追查中",
};
export const REVIEW_DECISION_LABELS: Record<string,string> = {
  false_positive: "判为误报",
  under_investigation: "判为待追查",
};
export const NAV_ITEMS = [
  { path:"/overview", icon:"01", label:"总览" },
  { path:"/datasets", icon:"02", label:"资产" },
  { path:"/analyses", icon:"03", label:"编排" },
  { path:"/reviews", icon:"04", label:"复核" },
  { path:"/governance", icon:"05", label:"治理" },
] as const;
