# 1. Ensure the Ubuntu Universe repository is enabled
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Add the ROS 2 GPG key
sudo apt update && sudo apt install curl gnupg lsb-release -y
sudo curl -sSL https://raw.githubusercontent.com/ros2/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# 3. Add the repository to your sources list
# Corrected repository entry command
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 4. Install ROS 2 packages (Desktop install includes rclpy)
sudo apt update
sudo apt upgrade -y
# Replace 'humble' with your target distro (e.g., jazzy) if on newer Ubuntu versions
sudo apt install ros-jazzy-desktop ros-dev-tools -y

# 5. Automatically source ROS 2 in every new terminal session
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc