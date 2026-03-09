import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getVideo,
  getVideoClips,
  getVideoStatus,
  listVideos,
  processVideo,
} from "../services/videoService";

export default function useVideo(videoId = "") {
  const queryClient = useQueryClient();
  const [liveStatus, setLiveStatus] = useState(null);

  const videosQuery = useQuery({
    queryKey: ["videos"],
    queryFn: listVideos,
    refetchInterval: 3000,
  });

  const processMutation = useMutation({
    mutationFn: processVideo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["videos"] }),
  });

  const statusQuery = useQuery({
    queryKey: ["video-status", videoId],
    queryFn: () => getVideoStatus(videoId),
    enabled: Boolean(videoId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === "done" || status === "error") {
        return false;
      }
      return 1500;
    },
  });

  const detailsQuery = useQuery({
    queryKey: ["video", videoId],
    queryFn: () => getVideo(videoId),
    enabled: Boolean(videoId),
    refetchInterval: 3000,
  });

  const clipsQuery = useQuery({
    queryKey: ["clips", videoId],
    queryFn: () => getVideoClips(videoId),
    enabled: Boolean(videoId),
    refetchInterval: 3000,
  });

  useEffect(() => {
    if (!videoId) {
      setLiveStatus(null);
      return undefined;
    }

    const token = localStorage.getItem("clipai_token");
    if (!token) {
      return undefined;
    }

    const apiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const wsBase = apiBase.startsWith("https://")
      ? apiBase.replace("https://", "wss://")
      : apiBase.replace("http://", "ws://");
    const wsUrl = `${wsBase}/video/${videoId}/ws?token=${encodeURIComponent(token)}`;

    let socket;
    try {
      socket = new WebSocket(wsUrl);
    } catch {
      return undefined;
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload && typeof payload === "object" && payload.status) {
          setLiveStatus(payload);
        }
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      if (socket && socket.readyState <= 1) {
        socket.close();
      }
    };
  }, [videoId]);

  return {
    videosQuery,
    processMutation,
    statusQuery,
    liveStatus,
    detailsQuery,
    clipsQuery,
  };
}
