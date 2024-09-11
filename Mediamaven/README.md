# Start
`sudo apt update && sudo apt upgrade -y`

# Adding Sublime Text 4
`wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/sublimehq-archive.gpg > /dev/null`

`echo "deb https://download.sublimetext.com/ apt/stable/" | sudo tee /etc/apt/sources.list.d/sublime-text.list`

# Install ZSH
`sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"`

# Additional Components
`sudo apt update && sudo apt install git python3-pip sublime-text chromium synaptic apt-transport-https xclip terminator cifs-utils byobu fzf docker.io docker-compose docker-compose-v2 tldr btop openssh-server zsh -y`

# Install Jellyfin
`curl https://repo.jellyfin.org/install-debuntu.sh | sudo bash`

# If I need to install ffmpeg
`wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v6.0.1-8/jellyfin-ffmpeg6_6.0.1-8-bookworm_arm64.deb`

# add bat alias for batcat (not always required)
`echo "alias bat='batcat'"`

# Remove libre office
`sudo apt-get remove --purge libreoffice\*`
`sudo apt-get clean`
`sudo apt-get autoremove`

# install SSH Server
`sudo apt-get install openssh-server`

# Optional Components
## Install Homebrew 
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

## Next Steps
- Run these two commands in your terminal to add Homebrew to your PATH:
    `(echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> /home/nexxsys/.bashrc
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`
- Install Homebrew's dependencies if you have sudo access:
    `sudo apt-get install build-essential`
  For more information, see:
    https://docs.brew.sh/Homebrew-on-Linux
- We recommend that you install GCC:
    `brew install gcc`
- Run brew help to get started
- Further documentation:
    https://docs.brew.sh

## Install jless
`https://formulae.brew.sh/formula/jless`

## install lsd and fonts
`brew install lsd`

`mkdir ~/.local/share/fonts
touch ~/.Xresources && echo "URxvt*font:    xft:Hack Nerd Font:style=Regular:size=11" >> ~/.Xresources
fc-cache -f -v`
