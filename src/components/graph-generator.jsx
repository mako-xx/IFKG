/**
 * v0 by Vercel.
 * @see https://v0.dev/t/VaX14modWQc
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
"use client";

import { useState } from 'react'; // 添加 useState 导入
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function GraphGenerator() {
  const [generateLoading, setGenerateLoading] = useState(false); // Add state for generating knowledge graph
  const [askLoading, setAskLoading] = useState(false); // Add state for asking question
  const [error, setError] = useState(''); // Add state management
  const [success, setSuccess] = useState(''); // Add state management
  const [question, setQuestion] = useState(''); // Add question state
  const [response, setResponse] = useState(''); // Add response state
  const [file, setFile] = useState(null); // Add file state
  const [fileName, setFileName] = useState(''); // Add file name state

  const handleGenerateGraph = async () => { // Add event handler
    setGenerateLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/generate-graph', {
        method: 'POST',
      });

      const result = await response.json();
      if (response.ok) {
        setSuccess(result.message);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setGenerateLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    setAskLoading(true);
    setError('');
    setResponse('');

    try {
      const response = await fetch('/api/ask-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: question })
      });

      const result = await response.json();
      if (response.ok) {
        setResponse(result.htmlResponse);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setAskLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };

  const handleFileClick = () => {
    document.getElementById('file-input').click();
  };

  return (
    <main className="flex flex-col items-center justify-center h-screen bg-gray-100 dark:bg-gray-900 p-6">
      <div className="max-w-6xl w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">Knowledge Graph Generator</h1>
            <p className="text-gray-500 dark:text-gray-400">Upload a CSV file and generate a knowledge graph.</p>
          </div>
          <div className="space-y-4">
            <div 
              className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 flex flex-col items-center justify-center space-y-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              onClick={handleFileClick}
            >
              {!fileName && (
                <>
                  <UploadIcon className="h-8 w-8 text-gray-500 dark:text-gray-400" />
                  <p className="text-gray-500 dark:text-gray-400">
                    Drag and drop your CSV file here or{" "}
                    <span className="text-blue-500 dark:text-blue-400 font-medium">browse</span>
                  </p>
                </>
              )}
              <input id="file-input" type="file" className="hidden" onChange={handleFileChange} />
              {fileName && <p className="text-gray-500 dark:text-gray-400">{fileName}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="openai-secret-key">OPEN_AI_SECRET_KEY</Label>
              <Input id="openai-secret-key" placeholder="Enter your OpenAI secret key" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="neo4j-uri">NEO4J_URI</Label>
              <Input id="neo4j-uri" placeholder="Enter your Neo4j URI" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="neo4j-username">NEO4J_USERNAME</Label>
              <Input id="neo4j-username" placeholder="Enter your Neo4j username" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="neo4j-password">NEO4J_PASSWORD</Label>
              <Input id="neo4j-password" placeholder="Enter your Neo4j password" type="password" />
            </div>
            {/* <Button className="w-full">Generate Knowledge Graph</Button> */}
            <Button className="w-full" onClick={handleGenerateGraph} disabled={generateLoading}>
              {generateLoading ? 'Generating...' : 'Generate Knowledge Graph'}
            </Button>
            {error && <p className="text-red-500">{error}</p>}
            {success && <p className="text-green-500">{success}</p>}
          </div>
        </div>
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">Ask a Question</h1>
            <p className="text-gray-500 dark:text-gray-400">
              Once you've generated a knowledge graph, you can ask questions about the data.
            </p>
          </div>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="question">Ask a question</Label>
              <div className="flex">
                <Input 
                  id="question" 
                  placeholder="Type your question here" 
                  className="flex-1" 
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
                <Button className="ml-2" onClick={handleAskQuestion} disabled={askLoading}>
                  {askLoading ? 'Asking...' : 'Ask'}
                </Button>
              </div>
            </div>
            <div className="border h-max border-gray-300 dark:border-gray-600 rounded-lg p-4 max-h-64 overflow-y-auto">
              <p className="text-gray-500 dark:text-gray-400">Response window for asking questions:</p>
              <div dangerouslySetInnerHTML={{ __html: response }} />
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}

function UploadIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" x2="12" y1="3" y2="15" />
    </svg>
  )
}