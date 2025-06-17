import time
import threading

g = 9.8  # 重力加速度，单位：m/s²
rebound_coefficient = 0.5  # 反弹系数
lock = threading.Lock()

# 获取初始高度
initial_height = float(input("请输入初始高度（米）: "))
current_height = initial_height
rebound_count = 0

time_elapsed = 0
falling = True
velocity = 0

# 监控线程专用变量
monitor_height = initial_height
monitor_velocity = 0
monitor_falling = True
monitor_time = 0

# 监控线程函数：独立计算0.1秒精度的高度
def precision_monitor():
    global monitor_height, monitor_velocity, monitor_falling, monitor_time
    while True:
        time.sleep(0.1)
        monitor_time += 0.1
        gap = 0.1
        
        # 使用半隐式欧拉法计算
        if monitor_falling:
            # 先更新速度再更新位置
            monitor_velocity += g * gap
            new_height = monitor_height - (monitor_velocity * gap - 0.5 * g * gap**2)
        else:
            # 上升阶段计算
            monitor_velocity -= g * gap
            new_height = monitor_height + (monitor_velocity * gap - 0.5 * g * gap**2)
        
        # 触地检测与反弹
        if new_height <= 0:
            monitor_height = 0
            monitor_falling = False
            # 正确计算反弹速度（考虑方向）
            monitor_velocity = abs(monitor_velocity) * rebound_coefficient
        else:
            monitor_height = new_height
        
        # 状态同步逻辑：每1秒（10次监控计算）同步一次主程序状态
        if int(monitor_time * 10) % 10 == 0:
            with lock:
                # 检测到主程序状态变化时进行校准
                if abs(monitor_height - current_height) > 0.01 or monitor_falling != falling:
                    monitor_height = current_height
                    monitor_velocity = velocity
                    monitor_falling = falling
        
        # 显示主程序值和高精度计算值
        with lock:
            print(f"[主程序值] {current_height:.2f}米 | [0.1秒演算值] {monitor_height:.4f}米")

# 启动监控线程
monitor_thread = threading.Thread(target=precision_monitor, daemon=True)
monitor_thread.start()

print(f"初始高度：{current_height:.2f}米")

try:
    while True:
        # 主程序保持1秒间隔计算
        gap = 1
        time.sleep(gap)
        time_elapsed += gap
        
        # 使用半隐式欧拉法计算
        if falling:
            # 先更新速度再更新位置
            velocity += g * gap
            new_height = current_height - (velocity * gap - 0.5 * g * gap**2)
        else:
            # 上升阶段计算
            velocity -= g * gap
            new_height = current_height + (velocity * gap - 0.5 * g * gap**2)
        
        # 触地检测与反弹
        if new_height <= 0:
            # 触地
            print("Boom")
            rebound_count += 1
            with lock:
                current_height = 0
            falling = False
            # 正确计算反弹速度（考虑方向）
            velocity = abs(velocity) * rebound_coefficient
        else:
            with lock:
                current_height = new_height
        
        # 检查反弹次数
        if rebound_count >= 3:
            print("End")
            break
except KeyboardInterrupt:
    print("程序已终止")