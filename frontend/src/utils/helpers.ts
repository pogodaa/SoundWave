// Форматирование времени в мм:сс
export const formatDuration = (seconds: number | null | undefined): string => {
      if (!seconds || isNaN(seconds)) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };
    
    // Генерация уникального ID для очереди
    export const generateQueueId = (): string => {
      return `queue_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    };