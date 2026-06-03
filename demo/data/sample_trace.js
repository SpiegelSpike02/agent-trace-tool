window.AGENT_TRACE_DEMO_DATA = {
  "schema_version": "agent-trace-v1",
  "generated_at": "2026-05-09T12:05:23.861688Z",
  "traces": [
    {
      "trace": {
        "id": "trace-week4-001",
        "project": "agent-debugger",
        "session_id": "session-demo-01",
        "user_id": "student-01",
        "start_time": "2026-05-06T09:00:00Z",
        "end_time": "2026-05-06T09:00:09.050000Z",
        "duration_ms": 9050.0,
        "context": {
          "input": "请帮我查询课程任务要求并整理提交材料",
          "system_prompt_hash": "sha256:demo",
          "conversation_turn": 3
        },
        "metadata": {},
        "tags": [
          "agent",
          "debug",
          "week4"
        ],
        "events": []
      },
      "summary": {
        "trace_id": "trace-week4-001",
        "span_count": 5,
        "completed_spans": 5,
        "tool_count": 2,
        "error_count": 1,
        "duration_ms": 9050.0,
        "prompt_tokens": 3724,
        "completion_tokens": 1168,
        "reasoning_tokens": 160,
        "cached_tokens": 432,
        "total_tokens": 5052
      },
      "issues": [
        {
          "severity": "error",
          "code": "span_error",
          "message": "tool span tool.search_docs failed: HTTP 429: rate limit exceeded.",
          "span_id": "span-search-tool",
          "recommendation": "展开该 span 的输入、输出和事件，定位异常参数或外部依赖。"
        },
        {
          "severity": "error",
          "code": "tool_failed",
          "message": "Tool search_docs failed: HTTP 429: rate limit exceeded.",
          "span_id": "span-search-tool",
          "recommendation": "记录工具入参、HTTP 状态码和重试策略，便于复现。"
        },
        {
          "severity": "warning",
          "code": "high_latency",
          "message": "Span CourseworkAgent.run took 8880 ms.",
          "span_id": "span-agent-root",
          "recommendation": "优先检查慢工具、检索器或模型调用的超时配置。"
        },
        {
          "severity": "warning",
          "code": "high_latency",
          "message": "Span tool.search_docs took 3500 ms.",
          "span_id": "span-search-tool",
          "recommendation": "优先检查慢工具、检索器或模型调用的超时配置。"
        },
        {
          "severity": "info",
          "code": "high_token_usage",
          "message": "Span CourseworkAgent.run consumed 2526 tokens.",
          "span_id": "span-agent-root",
          "recommendation": "检查上下文裁剪、检索片段数量和思考链记录粒度。"
        },
        {
          "severity": "info",
          "code": "high_token_usage",
          "message": "Span LLM.final_answer consumed 1750 tokens.",
          "span_id": "span-final-llm",
          "recommendation": "检查上下文裁剪、检索片段数量和思考链记录粒度。"
        }
      ],
      "tree": [
        {
          "id": "span-agent-root",
          "parent_id": null,
          "name": "CourseworkAgent.run",
          "kind": "agent",
          "status": "ok",
          "status_message": null,
          "start_time": "2026-05-06T09:00:00.120000Z",
          "end_time": "2026-05-06T09:00:09Z",
          "duration_ms": 8880.0,
          "tokens": {
            "prompt": 1862,
            "completion": 584,
            "reasoning": 80,
            "cached": 216,
            "total": 2526
          },
          "tool": null,
          "input": {
            "user_message": "请帮我查询课程任务要求并整理提交材料"
          },
          "output": {
            "deliverables": [
              "design.md",
              "agent_trace_core.zip"
            ],
            "tool_errors": 1
          },
          "attributes": {},
          "events": [
            {
              "name": "thought",
              "timestamp": "2026-05-06T09:00:00.260000Z",
              "message": "需要先理解任务，再拆成调研、设计、实现、打包四步。",
              "attributes": {}
            },
            {
              "name": "thought",
              "timestamp": "2026-05-06T09:00:05.220000Z",
              "message": "检索工具限流，改用缓存资料并标记工具失败。",
              "attributes": {}
            }
          ],
          "children": [
            {
              "id": "span-plan-llm",
              "parent_id": "span-agent-root",
              "name": "LLM.plan",
              "kind": "llm",
              "status": "ok",
              "status_message": null,
              "start_time": "2026-05-06T09:00:00.500000Z",
              "end_time": "2026-05-06T09:00:01.420000Z",
              "duration_ms": 920.0,
              "tokens": {
                "prompt": 612,
                "completion": 164,
                "reasoning": 0,
                "cached": 96,
                "total": 776
              },
              "tool": null,
              "input": {
                "model": "gpt-demo",
                "temperature": 0.2
              },
              "output": {
                "plan": [
                  "调研工具",
                  "定义日志规范",
                  "实现解析器",
                  "绘制Dashboard"
                ]
              },
              "attributes": {},
              "events": [],
              "children": []
            },
            {
              "id": "span-search-tool",
              "parent_id": "span-agent-root",
              "name": "tool.search_docs",
              "kind": "tool",
              "status": "error",
              "status_message": "HTTP 429: rate limit exceeded",
              "start_time": "2026-05-06T09:00:01.600000Z",
              "end_time": "2026-05-06T09:00:05.100000Z",
              "duration_ms": 3500.0,
              "tokens": {
                "prompt": 0,
                "completion": 0,
                "reasoning": 0,
                "cached": 0,
                "total": 0
              },
              "tool": {
                "name": "search_docs",
                "arguments": {
                  "query": "LangSmith Phoenix agent tracing design"
                },
                "call_id": null,
                "result": {
                  "retry_after_seconds": 2
                },
                "status": "error",
                "error": "HTTP 429: rate limit exceeded"
              },
              "input": null,
              "output": {
                "retry_after_seconds": 2
              },
              "attributes": {},
              "events": [
                {
                  "name": "tool_call",
                  "timestamp": "2026-05-06T09:00:01.600000Z",
                  "message": null,
                  "attributes": {
                    "tool": "search_docs",
                    "arguments": {
                      "query": "LangSmith Phoenix agent tracing design"
                    }
                  }
                },
                {
                  "name": "error",
                  "timestamp": "2026-05-06T09:00:05.100000Z",
                  "message": "HTTP 429: rate limit exceeded",
                  "attributes": {}
                }
              ],
              "children": []
            },
            {
              "id": "span-cache-tool",
              "parent_id": "span-agent-root",
              "name": "tool.read_cache",
              "kind": "tool",
              "status": "ok",
              "status_message": null,
              "start_time": "2026-05-06T09:00:05.450000Z",
              "end_time": "2026-05-06T09:00:05.980000Z",
              "duration_ms": 530.0,
              "tokens": {
                "prompt": 0,
                "completion": 0,
                "reasoning": 0,
                "cached": 0,
                "total": 0
              },
              "tool": {
                "name": "read_cache",
                "arguments": {
                  "topic": "agent observability"
                },
                "call_id": null,
                "result": {
                  "documents": 3,
                  "source": "local-cache"
                },
                "status": "ok",
                "error": null
              },
              "input": null,
              "output": {
                "documents": 3,
                "source": "local-cache"
              },
              "attributes": {},
              "events": [
                {
                  "name": "tool_call",
                  "timestamp": "2026-05-06T09:00:05.450000Z",
                  "message": null,
                  "attributes": {
                    "tool": "read_cache",
                    "arguments": {
                      "topic": "agent observability"
                    }
                  }
                }
              ],
              "children": []
            },
            {
              "id": "span-final-llm",
              "parent_id": "span-agent-root",
              "name": "LLM.final_answer",
              "kind": "llm",
              "status": "ok",
              "status_message": null,
              "start_time": "2026-05-06T09:00:06.150000Z",
              "end_time": "2026-05-06T09:00:08.800000Z",
              "duration_ms": 2650.0,
              "tokens": {
                "prompt": 1250,
                "completion": 420,
                "reasoning": 80,
                "cached": 120,
                "total": 1750
              },
              "tool": null,
              "input": {
                "context_chunks": 3,
                "model": "gpt-demo"
              },
              "output": {
                "answer": "已生成设计方案和核心代码包。"
              },
              "attributes": {},
              "events": [],
              "children": []
            }
          ]
        }
      ],
      "spans": [
        {
          "id": "span-agent-root",
          "parent_id": null,
          "name": "CourseworkAgent.run",
          "kind": "agent",
          "status": "ok",
          "status_message": null,
          "start_time": "2026-05-06T09:00:00.120000Z",
          "end_time": "2026-05-06T09:00:09Z",
          "duration_ms": 8880.0,
          "tokens": {
            "prompt": 1862,
            "completion": 584,
            "reasoning": 80,
            "cached": 216,
            "total": 2526
          },
          "tool": null,
          "input": {
            "user_message": "请帮我查询课程任务要求并整理提交材料"
          },
          "output": {
            "deliverables": [
              "design.md",
              "agent_trace_core.zip"
            ],
            "tool_errors": 1
          },
          "attributes": {},
          "events": [
            {
              "name": "thought",
              "timestamp": "2026-05-06T09:00:00.260000Z",
              "message": "需要先理解任务，再拆成调研、设计、实现、打包四步。",
              "attributes": {}
            },
            {
              "name": "thought",
              "timestamp": "2026-05-06T09:00:05.220000Z",
              "message": "检索工具限流，改用缓存资料并标记工具失败。",
              "attributes": {}
            }
          ],
          "children": [
            {
              "id": "span-plan-llm",
              "parent_id": "span-agent-root",
              "name": "LLM.plan",
              "kind": "llm",
              "status": "ok",
              "status_message": null,
              "start_time": "2026-05-06T09:00:00.500000Z",
              "end_time": "2026-05-06T09:00:01.420000Z",
              "duration_ms": 920.0,
              "tokens": {
                "prompt": 612,
                "completion": 164,
                "reasoning": 0,
                "cached": 96,
                "total": 776
              },
              "tool": null,
              "input": {
                "model": "gpt-demo",
                "temperature": 0.2
              },
              "output": {
                "plan": [
                  "调研工具",
                  "定义日志规范",
                  "实现解析器",
                  "绘制Dashboard"
                ]
              },
              "attributes": {},
              "events": [],
              "children": []
            },
            {
              "id": "span-search-tool",
              "parent_id": "span-agent-root",
              "name": "tool.search_docs",
              "kind": "tool",
              "status": "error",
              "status_message": "HTTP 429: rate limit exceeded",
              "start_time": "2026-05-06T09:00:01.600000Z",
              "end_time": "2026-05-06T09:00:05.100000Z",
              "duration_ms": 3500.0,
              "tokens": {
                "prompt": 0,
                "completion": 0,
                "reasoning": 0,
                "cached": 0,
                "total": 0
              },
              "tool": {
                "name": "search_docs",
                "arguments": {
                  "query": "LangSmith Phoenix agent tracing design"
                },
                "call_id": null,
                "result": {
                  "retry_after_seconds": 2
                },
                "status": "error",
                "error": "HTTP 429: rate limit exceeded"
              },
              "input": null,
              "output": {
                "retry_after_seconds": 2
              },
              "attributes": {},
              "events": [
                {
                  "name": "tool_call",
                  "timestamp": "2026-05-06T09:00:01.600000Z",
                  "message": null,
                  "attributes": {
                    "tool": "search_docs",
                    "arguments": {
                      "query": "LangSmith Phoenix agent tracing design"
                    }
                  }
                },
                {
                  "name": "error",
                  "timestamp": "2026-05-06T09:00:05.100000Z",
                  "message": "HTTP 429: rate limit exceeded",
                  "attributes": {}
                }
              ],
              "children": []
            },
            {
              "id": "span-cache-tool",
              "parent_id": "span-agent-root",
              "name": "tool.read_cache",
              "kind": "tool",
              "status": "ok",
              "status_message": null,
              "start_time": "2026-05-06T09:00:05.450000Z",
              "end_time": "2026-05-06T09:00:05.980000Z",
              "duration_ms": 530.0,
              "tokens": {
                "prompt": 0,
                "completion": 0,
                "reasoning": 0,
                "cached": 0,
                "total": 0
              },
              "tool": {
                "name": "read_cache",
                "arguments": {
                  "topic": "agent observability"
                },
                "call_id": null,
                "result": {
                  "documents": 3,
                  "source": "local-cache"
                },
                "status": "ok",
                "error": null
              },
              "input": null,
              "output": {
                "documents": 3,
                "source": "local-cache"
              },
              "attributes": {},
              "events": [
                {
                  "name": "tool_call",
                  "timestamp": "2026-05-06T09:00:05.450000Z",
                  "message": null,
                  "attributes": {
                    "tool": "read_cache",
                    "arguments": {
                      "topic": "agent observability"
                    }
                  }
                }
              ],
              "children": []
            },
            {
              "id": "span-final-llm",
              "parent_id": "span-agent-root",
              "name": "LLM.final_answer",
              "kind": "llm",
              "status": "ok",
              "status_message": null,
              "start_time": "2026-05-06T09:00:06.150000Z",
              "end_time": "2026-05-06T09:00:08.800000Z",
              "duration_ms": 2650.0,
              "tokens": {
                "prompt": 1250,
                "completion": 420,
                "reasoning": 80,
                "cached": 120,
                "total": 1750
              },
              "tool": null,
              "input": {
                "context_chunks": 3,
                "model": "gpt-demo"
              },
              "output": {
                "answer": "已生成设计方案和核心代码包。"
              },
              "attributes": {},
              "events": [],
              "children": []
            }
          ]
        },
        {
          "id": "span-plan-llm",
          "parent_id": "span-agent-root",
          "name": "LLM.plan",
          "kind": "llm",
          "status": "ok",
          "status_message": null,
          "start_time": "2026-05-06T09:00:00.500000Z",
          "end_time": "2026-05-06T09:00:01.420000Z",
          "duration_ms": 920.0,
          "tokens": {
            "prompt": 612,
            "completion": 164,
            "reasoning": 0,
            "cached": 96,
            "total": 776
          },
          "tool": null,
          "input": {
            "model": "gpt-demo",
            "temperature": 0.2
          },
          "output": {
            "plan": [
              "调研工具",
              "定义日志规范",
              "实现解析器",
              "绘制Dashboard"
            ]
          },
          "attributes": {},
          "events": [],
          "children": []
        },
        {
          "id": "span-search-tool",
          "parent_id": "span-agent-root",
          "name": "tool.search_docs",
          "kind": "tool",
          "status": "error",
          "status_message": "HTTP 429: rate limit exceeded",
          "start_time": "2026-05-06T09:00:01.600000Z",
          "end_time": "2026-05-06T09:00:05.100000Z",
          "duration_ms": 3500.0,
          "tokens": {
            "prompt": 0,
            "completion": 0,
            "reasoning": 0,
            "cached": 0,
            "total": 0
          },
          "tool": {
            "name": "search_docs",
            "arguments": {
              "query": "LangSmith Phoenix agent tracing design"
            },
            "call_id": null,
            "result": {
              "retry_after_seconds": 2
            },
            "status": "error",
            "error": "HTTP 429: rate limit exceeded"
          },
          "input": null,
          "output": {
            "retry_after_seconds": 2
          },
          "attributes": {},
          "events": [
            {
              "name": "tool_call",
              "timestamp": "2026-05-06T09:00:01.600000Z",
              "message": null,
              "attributes": {
                "tool": "search_docs",
                "arguments": {
                  "query": "LangSmith Phoenix agent tracing design"
                }
              }
            },
            {
              "name": "error",
              "timestamp": "2026-05-06T09:00:05.100000Z",
              "message": "HTTP 429: rate limit exceeded",
              "attributes": {}
            }
          ],
          "children": []
        },
        {
          "id": "span-cache-tool",
          "parent_id": "span-agent-root",
          "name": "tool.read_cache",
          "kind": "tool",
          "status": "ok",
          "status_message": null,
          "start_time": "2026-05-06T09:00:05.450000Z",
          "end_time": "2026-05-06T09:00:05.980000Z",
          "duration_ms": 530.0,
          "tokens": {
            "prompt": 0,
            "completion": 0,
            "reasoning": 0,
            "cached": 0,
            "total": 0
          },
          "tool": {
            "name": "read_cache",
            "arguments": {
              "topic": "agent observability"
            },
            "call_id": null,
            "result": {
              "documents": 3,
              "source": "local-cache"
            },
            "status": "ok",
            "error": null
          },
          "input": null,
          "output": {
            "documents": 3,
            "source": "local-cache"
          },
          "attributes": {},
          "events": [
            {
              "name": "tool_call",
              "timestamp": "2026-05-06T09:00:05.450000Z",
              "message": null,
              "attributes": {
                "tool": "read_cache",
                "arguments": {
                  "topic": "agent observability"
                }
              }
            }
          ],
          "children": []
        },
        {
          "id": "span-final-llm",
          "parent_id": "span-agent-root",
          "name": "LLM.final_answer",
          "kind": "llm",
          "status": "ok",
          "status_message": null,
          "start_time": "2026-05-06T09:00:06.150000Z",
          "end_time": "2026-05-06T09:00:08.800000Z",
          "duration_ms": 2650.0,
          "tokens": {
            "prompt": 1250,
            "completion": 420,
            "reasoning": 80,
            "cached": 120,
            "total": 1750
          },
          "tool": null,
          "input": {
            "context_chunks": 3,
            "model": "gpt-demo"
          },
          "output": {
            "answer": "已生成设计方案和核心代码包。"
          },
          "attributes": {},
          "events": [],
          "children": []
        }
      ]
    }
  ]
};
