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

  return {
    videosQuery,
    processMutation,
    statusQuery,
    detailsQuery,
    clipsQuery,
  };
}
