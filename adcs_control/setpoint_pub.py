import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy, QoSDurabilityPolicy
from std_msgs.msg import Int32MultiArray
import sys
import select
import time
import threading

class MinimalPublisher(Node):

    def __init__(self):
        super().__init__('setpoint_publisher')

        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=2,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE
        )

        self.publisher_ = self.create_publisher(Int32MultiArray, 'setpoint', qos_profile)
        self.timer_period = 0.01  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.setpoints = [0, 0, 0]  # Inicializa los setpoints de Yaw, Pitch y Roll
        self.last_increment_time = time.time()
        self.running = True

        # Start a background thread to listen for space key presses
        self.input_thread = threading.Thread(target=self.listen_for_input)
        self.input_thread.daemon = True
        self.input_thread.start()

    def timer_callback(self):
        msg = Int32MultiArray()
        msg.data = self.setpoints
        self.publisher_.publish(msg)
        # self.get_logger().info('Publishing: Yaw: %d, Pitch: %d, Roll: %d' % tuple(self.setpoints))

    def get_user_input(self):
        try:
            yaw = int(input("Ingrese el valor de Yaw: "))
            pitch = int(input("Ingrese el valor de Pitch: "))
            roll = int(input("Ingrese el valor de Roll: "))
            self.setpoints = [yaw, pitch, roll]
        except ValueError:
            self.get_logger().warn("Por favor, ingrese números válidos.")

    def increment_yaw(self):
        while self.setpoints[0] < 360:
            current_time = time.time()
            if current_time - self.last_increment_time >= self.timer_period:
                self.setpoints[0] = (self.setpoints[0] + 1) % 361  # Incrementa yaw y vuelve a 0 después de 360
                #self.setpoints[0] = 50 + 50 * np.cos(self.timer_period)
                self.last_increment_time = current_time
                #time.sleep(1)  # Espera 1 segundo entre incrementos

    def listen_for_input(self):
        while self.running:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key == ' ':
                    self.increment_yaw()
                elif key == '\n':
                    self.get_user_input()

def main(args=None):
    rclpy.init(args=args)

    setpoint_publisher = MinimalPublisher()

    try:
        while rclpy.ok():
            rclpy.spin_once(setpoint_publisher, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass

    setpoint_publisher.running = False
    setpoint_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()