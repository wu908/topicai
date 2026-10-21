-- 059_reference_anchor_accepted.sql（路径页「确认解读」的服务端持久化）
--
-- 参考锚点读出的结论被用户确认后，要跨刷新、跨设备记住。此前前端只写本机
-- localStorage，换浏览器/清站点数据就丢；服务端没有对应字段。
--
-- 只加一列 accepted_json（解读 value 的 JSON 数组），不改既有行：
--   - rejected_json 记「否证」，这一列记「确认」，两种决定分开存；
--   - 加列走 runner 的 _ensure_columns（PRAGMA 守卫，可重复执行），
--     SQL 本身保持空操作，避免旧库被重复 ALTER。
SELECT 1;
