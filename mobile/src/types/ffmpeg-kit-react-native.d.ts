declare module 'ffmpeg-kit-react-native' {
  export class ReturnCode {
    static isSuccess(code: ReturnCode | null): boolean;
  }

  export class FFmpegKit {
    static execute(command: string): Promise<FFmpegSession>;
  }

  export interface FFmpegSession {
    getReturnCode(): Promise<ReturnCode | null>;
    getAllLogsAsString(): Promise<string | null>;
  }
}
