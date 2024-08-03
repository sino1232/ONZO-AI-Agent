# ONZO AI Agent: The Multi-Agent

<p align="center">
<a href=""><img src="images/ONZO-AI-Agent.jpeg" alt="onzoGPT logo: Enable ONZO to work in software company, collaborating to tackle more complex tasks." width="450px"></a>
</p>

<p align="center">
<b>ONZO AI Agent: 당신과 함께 하는 조력자</b>
</p>

<p align="center">
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://huggingface.co/spaces/deepwisdom/MetaGPT" target="_blank"><img alt="Hugging Face" src="https://img.shields.io/badge/%F0%9F%A4%97%20-Hugging%20Face-blue?color=blue&logoColor=white" /></a>
</p>

ONZO AI Agent를 소개합니다.<br>
Groq(LPU)를 사용해 llama3-8b-8192 모델을 갖고 다양한 API서비스들을 호출하는 AI Agent를 구축했습니다.<br> 
Groq은 개인은 현재 무료입니다.<br>
이후에 혹시 유료가 되거나 사용이 어려울 경우 개인 자원(GPU 6GB이상 PC, 노트북, MACBOOK, 리눅스 등)을 사용해 개인 서버를 구축해 사용하려고 합니다.<br>
좋은 모델들이 나올때마다 Local LLM 모델을 업데이트할 예정입니다.<br>
Fine tuning, RAG 등을 통해서 구축할 수 있는 것들을 계속해서 적용해나가 보겠습니다.<br>
잘 사용해주시고 많은 아이디어 주시면 감사하겠습니다.<br>

온조라 지은 이유 TMI
1. 국사에서 가장 좋아하는 나라가 백제다.
2. AI Agent 초기시대이기에 백제 초대왕 온조왕을 차용했다.(2대왕이라고도 한다. 형 비류왕이 있어서)
3. N과 Z도 회전하면 같고 알파벳 O가 양쪽에 있어 안정감을 준다.
4. 개방적인 국가다.(중국과 일본과 활발한 교류를 했던 오픈마인드 국가)
5. 백제 왕 중 가장 업적이 많다.(초대왕이라 미화했다는 설도 있지만...)

## News

🌟 Aug. 3, 2024: First line of onzoAIagent code committed.

## Get Started

### Installation
> Python 3.10환경에서 만들었습니다.<br>
> Ensure that Python 3.10+ is installed on your system. You can check this by using: `python --version`.<br>
> You can use conda like this: `conda create -n onzo python=3.10 && conda activate onzo`

```bash
pip install --upgrade ONZO-AI-Agent
# or `pip install --upgrade git+https://github.com/sino1232/ONZO-AI-Agent.git`
# git clone https://github.com/sino1232/ONZO-AI-Agent && cd ONZO-AI-Agent    
# or `git clone https://github.com/sino1232/ONZO-AI-Agent && cd ONZO-AI-Agent && pip install --upgrade -e .
```

### 기능
1. 채팅봇 : telegram <br>
2. LLM : llama3-8b-8192
3. 자원 : groq LPU(현재까지 개인 무료) <br>
   https://groq.com/ <br>
4. news api <br>
   https://newsapi.org <br>
5. reddit api <br>
   https://www.reddit.com/dev/api/ <br>

### Configuration
```bash
# ONZO-AI-Agent/config/apikey.txt<br>
# 위 디렉토리에 있는 apikey.txt에서 모든 API 관련 key값을 설정하면 됩니다. 
```

### Usage

### QuickStart & Demo Video

## Tutorial

## Support

### Donation
안녕하세요. <br>
🐥가슴이 웅장해지는 모든것, 뱁새유니버스입니다.🐥<br>
모든 것에 관심이 많습니다.🌏<br>
세상에 긍정적인 영향을 끼치고 싶습니다.👍<br>
현명한 질문을 하려고 노력합니다.🙋🏻<br>
함께 배우고 성장하면 좋겠습니다.📈<br>
많은 사람들에게 도움이 될만한 일들을 찾아 제공할 수 있도록 노력하겠습니다.<br>
https://buymeacoffee.com/sino1232

### Contact Information
If you have any questions or feedback about this project, please feel free to contact us. We highly appreciate your suggestions!
- **Email:** livemylife9912@gmail.com
- **GitHub Issues:** For more technical inquiries, you can also create a new issue in our [GitHub repository](https://github.com/sino1232/ONZO-AI-Agent/)
We will respond to all questions within 2-3 business days.

## Citation

```bibtex
@inproceedings{hong2024metagpt,
      title={Meta{GPT}: Meta Programming for A Multi-Agent Collaborative Framework},
      author={Sirui Hong and Mingchen Zhuge and Jonathan Chen and Xiawu Zheng and Yuheng Cheng and Jinlin Wang and Ceyao Zhang and Zili Wang and Steven Ka Shing Yau and Zijuan Lin and Liyang Zhou and Chenyu Ran and Lingfeng Xiao and Chenglin Wu and J{\"u}rgen Schmidhuber},
      booktitle={The Twelfth International Conference on Learning Representations},
      year={2024},
      url={https://openreview.net/forum?id=VtmBAGCN7o}
}
```

