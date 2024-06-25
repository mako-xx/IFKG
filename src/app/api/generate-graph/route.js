// src/app/api/generate-graph/route.js
import { exec } from 'child_process';

export async function POST(req) {
  return new Promise((resolve) => {
    // 使用 && 确保命令按顺序执行
    const command = `
      source /opt/miniconda3/etc/profile.d/conda.sh && \
      conda activate createkg && \
      cd main && \
      cp .env.sample .env && \
      source .env && \
      python kg.py
    `;

    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`执行错误: ${error}`);
        resolve(new Response(JSON.stringify({ error: '生成知识图谱失败' }), { status: 500 }));
        return;
      }
      console.log(`标准输出: ${stdout}`);
      console.error(`标准错误: ${stderr}`);
      resolve(new Response(JSON.stringify({ message: '知识图谱生成成功' }), { status: 200 }));
    });
  });
}