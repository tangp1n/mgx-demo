import React, { useState, useEffect, useCallback } from "react";
import { Application } from "../../types/api";
import { applicationAPI } from "../../services/api";

interface CodeEditorProps {
  application: Application;
}

interface FileNode {
  name: string;
  type: "file" | "directory";
  path: string;
  size?: number;
  children?: FileNode[];
}

const CodeEditor: React.FC<CodeEditorProps> = ({ application }) => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(["/app"]));
  const [isGenerating, setIsGenerating] = useState(false);

  const applicationId = application._id || application.id || "";

  // Check if code generation is in progress based on application status
  useEffect(() => {
    const status = application.status;
    const generating = status === "generating" || status === "deploying" || status === "requirements_confirmed";
    setIsGenerating(generating);
  }, [application.status]);

  const loadFileTree = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await applicationAPI.getFileTree(applicationId);
      const files = response.files || [];
      setFileTree(files);

      // If we got files and were generating, stop polling
      if (files.length > 0 && isGenerating) {
        setIsGenerating(false);
      }
    } catch (err: any) {
      // Don't show error if container doesn't exist yet (code generation might not have started)
      if (err.response?.status === 404 || err.response?.status === 500) {
        const errorMsg = err.response?.data?.detail || "Failed to load file tree";
        // Only set error if we're not in generating state
        if (!isGenerating) {
          setError(errorMsg);
        }
      } else {
        setError(err.response?.data?.detail || "Failed to load file tree");
      }
    } finally {
      setLoading(false);
    }
  }, [applicationId, isGenerating]);

  useEffect(() => {
    loadFileTree();

    // If generating, poll for file tree updates every 3 seconds
    let pollInterval: NodeJS.Timeout | null = null;
    if (isGenerating) {
      pollInterval = setInterval(() => {
        loadFileTree();
      }, 3000);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [loadFileTree, isGenerating]);

  const loadFileContent = async (filePath: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await applicationAPI.getFileContent(applicationId, filePath);
      setFileContent(response.content);
      setSelectedFile(filePath);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load file content");
      setFileContent("");
    } finally {
      setLoading(false);
    }
  };

  const toggleDirectory = (path: string) => {
    setExpandedDirs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const renderFileTree = (nodes: FileNode[], level: number = 0) => {
    return nodes.map((node) => (
      <div key={node.path} style={{ marginLeft: `${level * 20}px` }}>
        {node.type === "directory" ? (
          <div>
            <div
              className="file-tree-directory"
              onClick={() => toggleDirectory(node.path)}
            >
              <span className="directory-icon">
                {expandedDirs.has(node.path) ? "📂" : "📁"}
              </span>
              <span className="directory-name">{node.name}</span>
            </div>
            {expandedDirs.has(node.path) && node.children && (
              <div className="directory-children">
                {renderFileTree(node.children, level + 1)}
              </div>
            )}
          </div>
        ) : (
          <div
            className={`file-tree-file ${
              selectedFile === node.path ? "selected" : ""
            }`}
            onClick={() => loadFileContent(node.path)}
          >
            <span className="file-icon">📄</span>
            <span className="file-name">{node.name}</span>
          </div>
        )}
      </div>
    ));
  };

  return (
    <div className="code-editor">
      <div className="code-editor-sidebar">
        <div className="file-tree-header">
          <h3>Files</h3>
          <button onClick={loadFileTree} className="refresh-button" title="Refresh">
            🔄
          </button>
        </div>
        {loading && !fileContent ? (
          <div className="loading">Loading...</div>
        ) : error && !fileTree.length && !isGenerating ? (
          <div className="error">{error}</div>
        ) : fileTree.length === 0 && isGenerating ? (
          <div className="code-generating">
            <p>🔄 代码生成中，请稍候...</p>
            <p className="generating-hint">文件将在生成完成后自动显示</p>
          </div>
        ) : fileTree.length === 0 ? (
          <div className="code-empty">
            <p>📁 暂无文件</p>
            <p className="empty-hint">
              {application.container_id
                ? "容器已创建，但还没有生成文件。请等待代码生成完成。"
                : "容器尚未创建。请先确认需求以生成代码。"}
            </p>
          </div>
        ) : (
          <div className="file-tree">{renderFileTree(fileTree)}</div>
        )}
      </div>

      <div className="code-editor-main">
        {selectedFile ? (
          <>
            <div className="file-header">
              <span className="file-path">{selectedFile}</span>
            </div>
            <div className="file-content">
              <pre>
                <code>{fileContent}</code>
              </pre>
            </div>
          </>
        ) : (
          <div className="code-editor-empty">
            <p>Select a file to view its content</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CodeEditor;
