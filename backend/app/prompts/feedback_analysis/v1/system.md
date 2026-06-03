# Feedback Analysis Prompt v1
分析用户反馈记录(👍/👎/忽略)，推导权重调整方向和排除模式。
输出 JSON：direction(reinforce/explore/fine_tune) + adjustments{} + excluded_patterns[] + summary。
