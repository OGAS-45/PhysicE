import time
import threading
import pygame
import sys
from pygame.locals import *

# 物理常量定义
GRAVITY = 9.8  # 重力加速度，单位：m/s²
REBOUND_COEFFICIENT = 1  # 反弹系数，值越小反弹高度越低

# 图形界面常量
SCREEN_WIDTH = 800  # 窗口宽度
SCREEN_HEIGHT = 600  # 窗口高度
GROUND_Y = SCREEN_HEIGHT - 50  # 地面位置
ball_radius = 20  # 小球半径
SCALE_FACTOR = 3  # 缩放因子，将米转换为像素

class FreeFallSimulator:
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("自由落体模拟")
        # 是不是默认值
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("SimHei", 24)
        self.small_font = pygame.font.SysFont("SimHei", 18)

        # 物理状态变量
        self.initial_height = 100.0  # 默认初始高度
        self.current_height = self.initial_height
        self.velocity = 0.0
        self.falling = True
        self.rebound_count = 0 # 跳跃次数
        self.time_elapsed = 0.0
        self.time_step = 0.1  # 默认时间步长
        
        # 新增水平运动相关变量
        self.horizontal_velocity = 5.0  # 初始水平速度，向右为正
        self.horizontal_rebound_coefficient = REBOUND_COEFFICIENT  # 水平反弹系数
        
        # 新增状态变量
        self.ball_x = SCREEN_WIDTH // 2  # 球的X坐标
        self.dragging = False  # 是否正在拖动
        self.drag_offset_x = 0  # 拖动时鼠标与球中心的X偏移
        self.drag_offset_y = 0  # 拖动时鼠标与球中心的Y偏移
        
        # 新增拖动惯性相关变量
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.last_mouse_time = 0
        
        # 控制变量
        self.running = True
        self.paused = False
        self.show_info = True
        self.lock = threading.Lock()

        # 创建并启动模拟线程
        self.simulation_thread = threading.Thread(target=self.simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def handle_events(self):
        """处理用户输入事件"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_SPACE:
                    self.paused = not self.paused
                elif event.key == K_i:
                    self.show_info = not self.show_info
                elif event.key == K_UP and self.time_step < 1.0:
                    self.time_step += 0.01
                elif event.key == K_DOWN and self.time_step > 0.01:
                    self.time_step -= 0.01
                elif event.key == K_r:
                    # 重置模拟
                    with self.lock:
                        self.current_height = self.initial_height
                        self.velocity = 5.0
                        self.falling = True
                        self.rebound_count = 0
                        self.time_elapsed = 0.0
                        # 重置水平速度
                        self.horizontal_velocity = 5.0
            # 新增鼠标事件处理
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 3:  # 右键点击
                    # 在鼠标位置创建新球
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    with self.lock:
                        # 计算鼠标位置对应的高度
                        # 这一段计算怎么理解？
                        # 首先，GROUND_Y是地面的Y坐标，也就是球的最大高度对应的Y坐标。
                        # 然后，减去ball_radius是为了让球的中心Y坐标与地面Y坐标对齐，而不是球的底部Y坐标与地面Y坐标对齐。
                        # 最后，除以SCALE_FACTOR是为了将高度从米转换为像素，因为我们的模拟是在米和像素之间进行转换的。
                        self.current_height = (GROUND_Y - ball_radius - mouse_y) / SCALE_FACTOR
                        self.initial_height = self.current_height
                        self.ball_x = mouse_x
                        self.velocity = 0.0
                        # 设置初始水平速度
                        self.horizontal_velocity = 5.0
                        self.rebound_count = 0
                        self.time_elapsed = 0.0
                elif event.button == 1:  # 左键点击
                    # 检查是否点击到球
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    ball_y = GROUND_Y - ball_radius - (self.current_height * SCALE_FACTOR)
                    # 计算鼠标与球中心的距离
                    distance = ((mouse_x - self.ball_x)**2 + (mouse_y - ball_y)** 2)**0.5
                    if distance <= ball_radius:
                        self.dragging = True
                        # 计算偏移量
                        self.drag_offset_x = self.ball_x - mouse_x
                        self.drag_offset_y = ball_y - mouse_y
                        # 记录初始拖动状态
                        self.last_mouse_x = mouse_x
                        self.last_mouse_y = mouse_y
                        self.last_mouse_time = pygame.time.get_ticks()
            elif event.type == MOUSEMOTION:
                # 拖动球
                if self.dragging:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    with self.lock:
                        # 更新球的位置
                        self.ball_x = mouse_x + self.drag_offset_x
                        new_ball_y = mouse_y + self.drag_offset_y
                        # 计算新高度
                        self.current_height = (GROUND_Y - ball_radius - new_ball_y) / SCALE_FACTOR
                        # 拖动时仅暂停垂直重力，保留水平速度计算
                        self.velocity = 0.0
                        self.falling = False  # 拖动时停止下落
                    # 实时更新鼠标状态，确保最后一刻速度准确
                    self.last_mouse_x = mouse_x
                    self.last_mouse_y = mouse_y
                    self.last_mouse_time = pygame.time.get_ticks()
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1 and self.dragging:
                    # 结束拖动
                    self.dragging = False
                    # 计算拖动速度
                    current_time = pygame.time.get_ticks()
                    time_diff = current_time - self.last_mouse_time
                    print(time_diff)
                    if time_diff > 10:  # 忽略极短时间拖动（<10ms）
                        # 获取当前鼠标位置
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        # 计算鼠标移动距离
                        dx = mouse_x - self.last_mouse_x
                        dy = mouse_y - self.last_mouse_y
                        
                        # 计算鼠标速度 (像素/毫秒) 并增加增益系数
                        mouse_velocity_x = dx / time_diff
                        mouse_velocity_y = dy / time_diff
                        
                        # 调整缩放因子和增益，增强惯性效果
                        scale = 1500.0 / SCALE_FACTOR  # 增加缩放比例
                        gain = 1.5  # 新增速度增益系数
                        self.horizontal_velocity = mouse_velocity_x * scale * gain
                        self.velocity = mouse_velocity_y * scale * gain  # 正值表示向下
                        
                        # 调整最大速度限制
                        max_velocity = 30.0  # 提高最大速度
                        self.horizontal_velocity = max(-max_velocity, min(self.horizontal_velocity, max_velocity))
                        self.velocity = max(-max_velocity, min(self.velocity, max_velocity))

    def simulation_loop(self):
        """物理模拟主循环"""
        # 主要都是time_step
        while self.running:
            if not self.paused and not self.dragging:  # 拖动时暂停模拟
                with self.lock:
                    # 计算垂直位移和速度
                    if self.falling:
                        # 下落阶段：先更新速度再更新位置
                        self.velocity += GRAVITY * self.time_step
                        displacement = self.velocity * self.time_step
                        self.current_height -= displacement
                    else:
                        # 上升阶段：先更新速度再更新位置
                        self.velocity -= GRAVITY * self.time_step
                        displacement = self.velocity * self.time_step
                        self.current_height += displacement

                    # 垂直方向触地检测与反弹
                    if self.current_height <= 0:
                        self.current_height = 0
                        self.falling = False
                        # 计算垂直反弹速度
                        self.velocity = abs(self.velocity) * REBOUND_COEFFICIENT
                        # 添加最小反弹速度阈值，避免无限小反弹
                        if self.velocity < 0.5:
                            self.velocity = 0
                        self.rebound_count += 1
                        print(f"反弹 {self.rebound_count} 次")

                    # 当上升速度减为0时，开始下落
                    if not self.falling and self.velocity <= 0:
                        self.falling = True
                        self.velocity = 0

                    # 新增水平方向运动
                    self.ball_x += self.horizontal_velocity * self.time_step

                    # 水平方向边界检测与反弹
                    # 左边界检测
                    if self.ball_x <= ball_radius:
                        self.ball_x = ball_radius  # 防止球超出边界
                        self.horizontal_velocity = abs(self.horizontal_velocity) * self.horizontal_rebound_coefficient
                    # 右边界检测
                    elif self.ball_x >= SCREEN_WIDTH - ball_radius:
                        self.ball_x = SCREEN_WIDTH - ball_radius  # 防止球超出边界
                        self.horizontal_velocity = -abs(self.horizontal_velocity) * self.horizontal_rebound_coefficient

                    self.time_elapsed += self.time_step

            # 控制模拟速度
            time.sleep(self.time_step)

    def draw(self):
        """绘制游戏界面"""
        # 清屏
        self.screen.fill((240, 240, 240))

        # 绘制地面
        pygame.draw.rect(self.screen, (50, 50, 50), (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))

        # 绘制小球
        with self.lock:
            # 计算小球在屏幕上的位置
            ball_y = GROUND_Y - ball_radius - (self.current_height * SCALE_FACTOR)
            pygame.draw.circle(self.screen, (255, 255, 0), (self.ball_x, int(ball_y)), ball_radius)
            
            # 标注球的信息
            ball_info = self.small_font.render(f"{self.current_height:.1f}m", True, (0, 0, 0))
            info_rect = ball_info.get_rect(center=(self.ball_x, int(ball_y)))
            self.screen.blit(ball_info, info_rect)
        
        # 绘制信息文本
        if self.show_info:
            with self.lock:
                height_text = self.font.render(f"高度: {self.current_height:.2f} 米", True, (0, 0, 0))
                velocity_text = self.font.render(f"速度: {abs(self.velocity):.2f} m/s", True, (0, 0, 0))
                time_text = self.font.render(f"时间: {self.time_elapsed:.2f} 秒", True, (0, 0, 0))
                rebound_text = self.font.render(f"反弹次数: {self.rebound_count}", True, (0, 0, 0))
                step_text = self.small_font.render(f"时间步长: {self.time_step:.2f}秒 (↑↓调整)", True, (0, 0, 0))
                info_text = self.small_font.render("空格:暂停/继续 | I:显示/隐藏信息 | R:重置 | ESC:退出", True, (0, 0, 0))

                self.screen.blit(height_text, (10, 10))
                self.screen.blit(velocity_text, (10, 40))
                self.screen.blit(time_text, (10, 70))
                self.screen.blit(rebound_text, (10, 100))
                self.screen.blit(step_text, (10, SCREEN_HEIGHT - 40))
                self.screen.blit(info_text, (10, SCREEN_HEIGHT - 20))

        # 更新显示
        pygame.display.flip()

    def run(self):
        """运行模拟主循环"""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)  # 限制帧率
        pygame.quit()
        sys.exit()

if __name__ == "__main__":

    initial_height = 100.0

    # 创建并运行模拟器
    simulator = FreeFallSimulator()
    simulator.initial_height = initial_height
    simulator.current_height = initial_height

    # 初始化结束
    simulator.run()