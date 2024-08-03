# ONZO AI Agent: The Multi-Agent

<p align="center">
<a href=""><img src="images/ONZO-AI-Agent.jpeg" alt="onzoGPT logo: Enable ONZO to work in software company, collaborating to tackle more complex tasks." width="450px"></a>
</p>

<p align="center">
<b>당신을 위해 일하는 ONZO AI Agent</b>
</p>

<p align="center">
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://huggingface.co/spaces/deepwisdom/MetaGPT" target="_blank"><img alt="Hugging Face" src="https://img.shields.io/badge/%F0%9F%A4%97%20-Hugging%20Face-blue?color=blue&logoColor=white" /></a>
</p>

ONZO AI Agent를 소개합니다.

온조라 지은 이유 TMI
1. 국사에서 가장 좋아하는 나라가 백제다.
2. AI Agent 초기시대이기에 백제 초대왕 온조왕을 차용했다.(2대왕이라고도 한다. 형 비류왕이 있어서)
3. N과 Z도 회전하면 같고 알파벳 O가 양쪽에 있어 안정감을 준다.
4. 개방적인 국가다.(중국과 일본과 활발한 교류를 했던 오픈마인드 국가)
5. 백제 왕 중 가장 업적이 많다.(초대왕이라 미화했다는 설도 있지만...)


ONZO-AI-Agent/config/apikey.txt<br>


## News

🌟 Aug. 3, 2024: First line of onzoAIagent code committed.

## Get Started

### Installation

> Ensure that Python 3.9+ is installed on your system. You can check this by using: `python --version`.  
> You can use conda like this: `conda create -n metagpt python=3.9 && conda activate metagpt`

```bash
pip install --upgrade metagpt
# or `pip install --upgrade git+https://github.com/geekan/MetaGPT.git`
# or `git clone https://github.com/geekan/MetaGPT && cd MetaGPT && pip install --upgrade -e .`
```

For detailed installation guidance, please refer to [cli_install](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html#install-stable-version)
 or [docker_install](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html#install-with-docker)

1. telegram <br>
2. groq <br>
   https://groq.com/ <br>
3. news api <br>
   https://newsapi.org <br>

### Configuration

You can init the config of MetaGPT by running the following command, or manually create `~/.metagpt/config2.yaml` file:
```bash
# Check https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html for more details
metagpt --init-config  # it will create ~/.metagpt/config2.yaml, just modify it to your needs
```

You can configure `~/.metagpt/config2.yaml` according to the [example](https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml) and [doc](https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html):

```yaml
llm:
  api_type: "openai"  # or azure / ollama / groq etc. Check LLMType for more options
  model: "gpt-4-turbo"  # or gpt-3.5-turbo
  base_url: "https://api.openai.com/v1"  # or forward url / other llm url
  api_key: "YOUR_API_KEY"
```

### Usage

After installation, you can use MetaGPT at CLI

```bash
metagpt "Create a 2048 game"  # this will create a repo in ./workspace
```

or use it as library

```python
from metagpt.software_company import generate_repo, ProjectRepo
repo: ProjectRepo = generate_repo("Create a 2048 game")  # or ProjectRepo("<path>")
print(repo)  # it will print the repo structure with files
```

You can also use [Data Interpreter](https://github.com/geekan/MetaGPT/tree/main/examples/di) to write code:

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main():
    di = DataInterpreter()
    await di.run("Run data analysis on sklearn Iris dataset, include a plot")

asyncio.run(main())  # or await main() in a jupyter notebook setting
```


### QuickStart & Demo Video
- Try it on [MetaGPT Huggingface Space](https://huggingface.co/spaces/deepwisdom/MetaGPT)
- [Matthew Berman: How To Install MetaGPT - Build A Startup With One Prompt!!](https://youtu.be/uT75J_KG_aY)
- [Official Demo Video](https://github.com/geekan/MetaGPT/assets/2707039/5e8c1062-8c35-440f-bb20-2b0320f8d27d)

https://github.com/geekan/MetaGPT/assets/34952977/34345016-5d13-489d-b9f9-b82ace413419

## Tutorial

## Support

### Contributor form

### Contact Information

If you have any questions or feedback about this project, please feel free to contact us. We highly appreciate your suggestions!

- **Email:** livemylife9912@gmail.com
- **GitHub Issues:** For more technical inquiries, you can also create a new issue in our [GitHub repository](https://github.com/geekan/metagpt/issues).
- 
We will respond to all questions within 2-3 business days.

## Citation

To stay updated with the latest research and development, follow [@MetaGPT_](https://twitter.com/MetaGPT_) on Twitter. 

To cite [MetaGPT](https://openreview.net/forum?id=VtmBAGCN7o) or [Data Interpreter](https://arxiv.org/abs/2402.18679) in publications, please use the following BibTeX entries.

```bibtex
@inproceedings{hong2024metagpt,
      title={Meta{GPT}: Meta Programming for A Multi-Agent Collaborative Framework},
      author={Sirui Hong and Mingchen Zhuge and Jonathan Chen and Xiawu Zheng and Yuheng Cheng and Jinlin Wang and Ceyao Zhang and Zili Wang and Steven Ka Shing Yau and Zijuan Lin and Liyang Zhou and Chenyu Ran and Lingfeng Xiao and Chenglin Wu and J{\"u}rgen Schmidhuber},
      booktitle={The Twelfth International Conference on Learning Representations},
      year={2024},
      url={https://openreview.net/forum?id=VtmBAGCN7o}
}
@misc{hong2024data,
      title={Data Interpreter: An LLM Agent For Data Science}, 
      author={Sirui Hong and Yizhang Lin and Bang Liu and Bangbang Liu and Binhao Wu and Danyang Li and Jiaqi Chen and Jiayi Zhang and Jinlin Wang and Li Zhang and Lingyao Zhang and Min Yang and Mingchen Zhuge and Taicheng Guo and Tuo Zhou and Wei Tao and Wenyi Wang and Xiangru Tang and Xiangtao Lu and Xiawu Zheng and Xinbing Liang and Yaying Fei and Yuheng Cheng and Zongze Xu and Chenglin Wu},
      year={2024},
      eprint={2402.18679},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
```

