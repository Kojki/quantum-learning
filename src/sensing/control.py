class PIDController:
    """量子センシング用 PID制御クラス
    P (Proportional): 現在の誤差に比例
    I (Integral): 過去の累積誤差を解消（定常偏差の除去）
    D (Derivative): 誤差の変化率を抑える（振動の抑制）
    """

    def __init__(self, Kp=0.4, Ki=0.05, Kd=0.1):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        self.integral = 0
        self.prev_error = 0

    def update(self, error, dt=1.0):
        # 積分項
        self.integral += error * dt
        # 微分項
        derivative = (error - self.prev_error) / dt
        # 合計の出力
        output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)
        # 前回の誤差を更新
        self.prev_error = error
        return output

    def reset(self):
        """状態をリセットする"""
        self.integral = 0
        self.prev_error = 0
