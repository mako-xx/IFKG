import { exec } from 'child_process';
import { readFile } from 'fs/promises';

export async function POST(req) {
  const { query } = await req.json();

  return new Promise((resolve) => {
    const command = `
      source /opt/miniconda3/etc/profile.d/conda.sh && \
      conda activate createkg && \
      cd main && \
      cp .env.sample .env && \
      source .env && \
      python qa.py "${query}"
    `;

    exec(command, async (error) => {
      if (error) {
        console.error(`Execution error: ${error}`);
        resolve(new Response(JSON.stringify({ error: 'Failed to generate knowledge graph' }), { status: 500 }));
        return;
      }
      
      try {
        const htmlResponse = await readFile('main/html_response.txt', 'utf-8');
        resolve(new Response(JSON.stringify({ htmlResponse }), { status: 200 }));
      } catch (readError) {
        console.error(`Read file error: ${readError}`);
        resolve(new Response(JSON.stringify({ error: 'Failed to read the response file' }), { status: 500 }));
      }
    });
  });
}