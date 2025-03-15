#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import SpotifyWebApi from 'spotify-web-api-node';

interface AudioFeatures {
  danceability: number;
  energy: number;
  key: number;
  loudness: number;
  mode: number;
  speechiness: number;
  acousticness: number;
  instrumentalness: number;
  liveness: number;
  valence: number;
  tempo: number;
  duration_ms: number;
  [key: string]: any;
}

class SpotifyServer {
  private server: Server;
  private spotifyApi: SpotifyWebApi;
  private static readonly BATCH_SIZE = 100;
  private static readonly MAX_RETRIES = 3;
  private static readonly RETRY_DELAY = 5000;

  constructor() {
    // Initialize MCP Server
    this.server = new Server(
      {
        name: 'spotify-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize Spotify API client
    this.spotifyApi = new SpotifyWebApi({
      clientId: process.env.SPOTIFY_CLIENT_ID,
      clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
    });

    this.setupToolHandlers();
    this.server.onerror = (error) => console.error('[MCP Error]', error);
  }

  private validateAudioFeatures(features: any): boolean {
    const requiredFeatures = [
      'danceability', 'energy', 'key', 'loudness', 'mode',
      'speechiness', 'acousticness', 'instrumentalness',
      'liveness', 'valence', 'tempo', 'duration_ms'
    ];
    
    return features && requiredFeatures.every(feature => 
      feature in features && features[feature] !== null
    );
  }

  private async refreshAccessToken(): Promise<void> {
    try {
      const data = await this.spotifyApi.clientCredentialsGrant();
      this.spotifyApi.setAccessToken(data.body.access_token);
    } catch (error) {
      throw new McpError(
        ErrorCode.AuthenticationError,
        'Failed to refresh access token'
      );
    }
  }

  private async fetchWithRetry<T>(
    operation: () => Promise<T>,
    retries = SpotifyServer.MAX_RETRIES
  ): Promise<T> {
    try {
      return await operation();
    } catch (error: any) {
      if (error.statusCode === 401) {
        await this.refreshAccessToken();
        return this.fetchWithRetry(operation, retries - 1);
      }
      if (error.statusCode === 429) {
        const retryAfter = parseInt(error.headers['retry-after'] || '5') * 1000;
        await new Promise(resolve => setTimeout(resolve, retryAfter));
        return this.fetchWithRetry(operation, retries);
      }
      if (retries > 0) {
        await new Promise(resolve => 
          setTimeout(resolve, SpotifyServer.RETRY_DELAY)
        );
        return this.fetchWithRetry(operation, retries - 1);
      }
      throw error;
    }
  }

  private async getAudioFeatures(trackIds: string[]): Promise<AudioFeatures[]> {
    const features: AudioFeatures[] = [];
    
    for (let i = 0; i < trackIds.length; i += SpotifyServer.BATCH_SIZE) {
      const batch = trackIds.slice(i, i + SpotifyServer.BATCH_SIZE);
      const response = await this.fetchWithRetry(async () => {
        const data = await this.spotifyApi.getAudioFeaturesForTracks(batch);
        return data.body.audio_features;
      });

      features.push(...response.map(feature => 
        this.validateAudioFeatures(feature) ? feature : null
      ));
    }

    return features;
  }

  private setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'get_audio_features',
          description: 'Get audio features for multiple tracks',
          inputSchema: {
            type: 'object',
            properties: {
              track_ids: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of Spotify track IDs or URIs',
              },
            },
            required: ['track_ids'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      if (request.params.name !== 'get_audio_features') {
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${request.params.name}`
        );
      }

      const { track_ids } = request.params.arguments as { track_ids: string[] };
      
      // Validate track IDs and convert URIs if needed
      const processedIds = track_ids.map(id => {
        if (id.startsWith('spotify:track:')) {
          return id.split(':').pop();
        }
        return id;
      });

      try {
        const features = await this.getAudioFeatures(processedIds);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(features, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error fetching audio features: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Spotify MCP server running on stdio');
  }
}

const server = new SpotifyServer();
server.run().catch(console.error);