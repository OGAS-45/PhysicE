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
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("SimHei", 24)
        self.small_font = pygame.font.SysFont("SimHei", 18)

        # 物理状态变量
        self.initial_height = 100.0  # 默认初始高度
        self.current_height = self.initial_height
        self.velocity = 0.0
        self.falling = True
        self.rebound_count = 0
        self.time_elapsed = 0.0
        self.time_step = 0.1  # 默认时间步长
        
        # 新增状态变量
        self.ball_x = SCREEN_WIDTH // 2  # 球的X坐标
        self.dragging = False  # 是否正在拖动
        self.drag_offset_x = 0  # 拖动时鼠标与球中心的X偏移
        self.drag_offset_y = 0  # 拖动时鼠标与球中心的Y偏移
        
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
                        self.velocity = 0.0
                        self.falling = True
                        self.rebound_count = 0
                        self.time_elapsed = 0.0
            # 新增鼠标事件处理
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 3:  # 右键点击
                    # 在鼠标位置创建新球
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    with self.lock:
                        # 计算鼠标位置对应的高度
                        self.current_height = (GROUND_Y - ball_radius - mouse_y) / SCALE_FACTOR
                        self.initial_height = self.current_height
                        self.ball_x = mouse_x
                        self.velocity = 0.0
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
                        # 停止当前运动
                        self.velocity = 0.0
                        self.falling = True
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1 and self.dragging:
                    # 结束拖动
                    self.dragging = False

    def simulation_loop(self):
        """物理模拟主循环"""
        while self.running:
            if not self.paused and not self.dragging:  # 拖动时暂停模拟
                with self.lock:
                    # 计算位移和速度
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

                    # 触地检测与反弹
                    if self.current_height <= 0:
                        self.current_height = 0
                        self.falling = False
                        # 计算反弹速度（考虑能量损失和最小反弹阈值）
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
            pygame.draw.circle(self.screen, (255, 0, 0), (self.ball_x, int(ball_y)), ball_radius)
            
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
    # 获取初始高度
    try:
        initial_height = float(input("请输入初始高度（米）: "))
        if initial_height <= 0:
            print("初始高度必须为正数，将使用默认值100米")
            initial_height = 100.0
    except ValueError:
        print("输入无效，将使用默认值100米")
        initial_height = 100.0

    # 创建并运行模拟器
    simulator = FreeFallSimulator()
    simulator.initial_height = initial_height
    simulator.current_height = initial_height
    simulator.run()