import express from 'express';
import { Server } from 'http';
import { Request, Response, NextFunction } from 'express';
import { EthereumRoutes } from './chains/ethereum/ethereum.routes';
import { UniswapRoutes } from './chains/ethereum/uniswap/uniswap.routes';
import { ConfigManager } from './services/config-manager';
import { logger, updateLoggerToStdout } from './services/logger';
import { addHttps } from './https';
import {
  asyncHandler,
  HttpException,
  NodeError,
} from './services/error-handler';

export const app = express();
let server: Server;

// parse body for application/json
app.use(express.json());

// parse url for application/x-www-form-urlencoded
app.use(express.urlencoded({ extended: true }));

// mount sub routers
app.use('/eth', EthereumRoutes.router);
app.use('/eth/uniswap', UniswapRoutes.router);

// a simple route to test that the server is running
app.get('/', (_req: Request, res: Response) => {
  res.status(200).json({ status: 'ok' });
});

app.get(
  '/config',
  (_req: Request, res: Response<ConfigManager.Config, any>) => {
    res.status(200).json(ConfigManager.config);
  }
);

interface ConfigUpdateRequest {
  APPNAME?: string;
  PORT?: number;
  IP_WHITELIST?: string[];
  HUMMINGBOT_INSTANCE_ID?: string;
  LOG_PATH?: string;
  GMT_OFFSET: number;
  CERT_PATH?: string;
  CERT_PASSPHRASE?: string;
  ETHEREUM_CHAIN?: string;
  INFURA_KEY?: string;
  ETH_GAS_STATION_ENABLE?: boolean;
  ETH_GAS_STATION_API_KEY?: string;
  ETH_GAS_STATION_GAS_LEVEL?: string;
  ETH_GAS_STATION_REFRESH_TIME?: number;
  ETH_MANUAL_GAS_PRICE?: number;
  LOG_TO_STDOUT?: boolean;
}

app.post(
  '/config/update',
  asyncHandler(
    async (
      req: Request<unknown, unknown, ConfigUpdateRequest>,
      res: Response
    ) => {
      const config = ConfigManager.config;

      for (const [k, v] of Object.entries(req.body)) {
        // this prevents the client from accidentally turning off HTTPS
        if (k != 'UNSAFE_DEV_MODE_WITH_HTTP' && k != 'VERSION' && k in config) {
          (config as any)[k] = v;
        }
      }

      logger.info('Update gateway config file.');
      ConfigManager.updateConfig(config);

      logger.info('Reloading gateway config file.');
      ConfigManager.reloadConfig();

      logger.info('Reload logger to stdout.');
      updateLoggerToStdout();

      logger.info('Reloading Ethereum routes.');
      EthereumRoutes.reload();

      logger.info('Restarting gateway.');
      await stopGateway();
      await startGateway();

      res.status(200).json({ message: 'The config has been updated' });
    }
  )
);

// handle any error thrown in the gateway api route
app.use(
  (
    err: Error | NodeError | HttpException,
    _req: Request,
    res: Response,
    _next: NextFunction
  ) => {
    const response: any = {
      message: err.message || 'Unknown error.',
    };
    if (err.stack) response.stack = err.stack;
    let httpErrorCode = 500;
    if (err instanceof HttpException) {
      httpErrorCode = err.status;
      response.errorCode = err.errorCode;
    } else if ('code' in err) {
      httpErrorCode = 503;
      response.errorCode = 1099;
      response.message = 'Unknown error.';

      switch (typeof err.code) {
        case 'string':
          // error is from ethers library
          if (['NETWORK_ERROR', 'SERVER_ERROR', 'TIMEOUT'].includes(err.code)) {
            response.errorCode = 1001;
            response.message =
              'Network error. Please check your node URL, API key, and Internet connection.';
          }
          break;

        case 'number':
          // errors from provider
          if (err.code === -32005) {
            // we only handle rate-limit errors
            response.errorCode = 1002;
            response.message = 'Blockchain node API rate limit exceeded.';
          }
          break;
      }
    }
    if (err instanceof HttpException) {
      httpErrorCode = err.status;
    }
    logger.error(response.message + '\n' + response.stack);
    return res.status(httpErrorCode).json(response);
  }
);

export const startGateway = async () => {
  const port = ConfigManager.config.PORT;
  logger.info(`⚡️ Gateway API listening on port ${port}`);
  if (ConfigManager.config.UNSAFE_DEV_MODE_WITH_HTTP) {
    logger.info('Running in UNSAFE HTTP! This could expose private keys.');
    server = await app.listen(port);
  } else {
    logger.info('The server is secured behind HTTPS.');
    server = await addHttps(app).listen(port);
  }
};

const stopGateway = async () => {
  return server.close();
};
