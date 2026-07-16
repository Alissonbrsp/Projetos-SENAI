# Build do Yocto Linux para Intel Galileo Gen 2

## Pré-requisitos

- Ubuntu 18.04 LTS (recomendado para Dunfell)
- 100+ GB de espaço em disco
- 8+ GB de RAM
- Conexão à internet

## 1. Instalar dependências do sistema

```bash
sudo apt-get update
sudo apt-get install -y gawk wget git diffstat unzip texinfo gcc build-essential \
  chrpath socat cpio python3 python3-pip python3-pexpect xz-utils debianutils \
  iputils-ping python3-setuptools python3-git python3-jinja2 libegl1-mesa \
  libsdl1.2-dev pylint3 xterm rsync curl
```

## 2. Clonar as camadas Yocto

```bash
cd ~

# Poky (base do Yocto)
git clone git://git.yoctoproject.org/poky
cd poky && git checkout -b dunfell origin/dunfell && cd ..

# meta-openembedded (pacotes extras: nano, python3, i2c-tools, etc.)
git clone git://git.openembedded.org/meta-openembedded
cd meta-openembedded && git checkout -b dunfell origin/dunfell && cd ..

# meta-intel-quark (BSP do Galileo Gen 2)
git clone https://github.com/kraj/meta-intel-iot-middleware meta-intel-quark
cd meta-intel-quark && git checkout -b dunfell origin/dunfell && cd ..
```

## 3. Inicializar o ambiente de build

```bash
cd ~/poky
source oe-init-build-env
# Agora você está em ~/poky/build/
```

## 4. Copiar as configurações do projeto

```bash
# A partir do diretório raiz do repositório CTF:
cp edge-device/yocto/local.conf   ~/poky/build/conf/local.conf
cp edge-device/yocto/bblayers.conf ~/poky/build/conf/bblayers.conf

# Ajuste os caminhos em bblayers.conf se necessário
nano ~/poky/build/conf/bblayers.conf
```

## 5. Adicionar as camadas via bitbake-layers

```bash
cd ~/poky/build
bitbake-layers add-layer ../meta-openembedded/meta-oe
bitbake-layers add-layer ../meta-openembedded/meta-python
bitbake-layers add-layer ../meta-openembedded/meta-networking
bitbake-layers add-layer ../meta-intel-quark
```

## 6. Compilar a imagem

```bash
bitbake core-image-full-cmdline
```

> ⏱️ O primeiro build leva **4 a 8 horas** dependendo do hardware. Builds subsequentes são muito mais rápidos graças ao cache (sstate-cache).

## 7. Localizar a imagem gerada

```bash
ls tmp/deploy/images/intel-galileo-gen2/*.hddimg
# Ex: core-image-full-cmdline-intel-galileo-gen2.hddimg
```

## 8. Gravar no cartão SD

Use o **BalenaEtcher** (recomendado):
1. Baixe em https://www.balena.io/etcher/
2. Selecione o arquivo `.hddimg`
3. Selecione o cartão SD (cuidado para não selecionar o HD!)
4. Clique em **Flash!**

Ou via linha de comando (`dd`):
```bash
# Identifique o dispositivo do SD com: lsblk
sudo dd if=core-image-full-cmdline-intel-galileo-gen2.hddimg \
     of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

## 9. Primeiro boot

1. Insira o SD card no Galileo Gen 2
2. Conecte o cabo Ethernet
3. Ligue a alimentação (7-15V DC)
4. Descubra o IP via seu roteador ou `nmap -sn 192.168.1.0/24`
5. Acesse via SSH: `ssh jao@<IP_DO_GALILEO>` (senha: `galileo123`)

## 10. Configurar o sensor

```bash
# No Galileo, após o SSH:
pip3 install paho-mqtt smbus2

# Enviar o script do sensor via scp (do seu PC):
scp edge-device/scripts/sensor.py jao@<IP_GALILEO>:~/

# Configurar e rodar:
ssh jao@<IP_GALILEO>
nano ~/sensor.py        # Ajuste o IP do broker (VM2)
python3 ~/sensor.py --debug   # Testar
python3 ~/sensor.py --simulate # Modo simulação (sem sensores físicos)
```

## Especificações do SO Gerado

| Atributo | Valor |
|----------|-------|
| Versão Yocto | Dunfell 3.1.33 |
| Kernel | 3.8.7 (patched para Quark X1000) |
| Arquitetura | i586 (32-bit x86) |
| Interface | CLI apenas (sem GUI) |
| Acesso remoto | OpenSSH |
| Python | 3.x com pip |
| Compilador | gcc/g++ (tools-sdk) |
| I2C | i2c-tools + python3-smbus2 |
| MQTT libs | paho-mqtt-c, paho-mqtt-cpp |
