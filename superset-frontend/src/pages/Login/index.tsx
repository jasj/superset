/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { t } from '@apache-superset/core';
import { SupersetClient } from '@superset-ui/core';
import { styled, css } from '@apache-superset/core/ui';
import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Typography,
  Icons,
} from '@superset-ui/core/components';
import { useState, useEffect, useMemo } from 'react';
import { capitalize } from 'lodash/fp';
import { addDangerToast } from 'src/components/MessageToasts/actions';
import { useDispatch } from 'react-redux';
import getBootstrapData from 'src/utils/getBootstrapData';

type OAuthProvider = {
  name: string;
  icon: string;
};

type OIDProvider = {
  name: string;
  url: string;
};

type Provider = OAuthProvider | OIDProvider;

interface LoginForm {
  username: string;
  password: string;
}

enum AuthType {
  AuthOID = 0,
  AuthDB = 1,
  AuthLDAP = 2,
  AuthOauth = 4,
}

const LoginContainer = styled.div`
  ${({ theme }) => css`
    width: 100%;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, ${theme.colorPrimary}15 0%, ${theme.colorPrimaryBg} 100%);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      width: 200%;
      height: 200%;
      background: radial-gradient(
        circle,
        ${theme.colorPrimary}08 0%,
        transparent 70%
      );
      animation: pulse 15s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% {
        transform: translate(-50%, -50%) scale(1);
        opacity: 1;
      }
      50% {
        transform: translate(-50%, -50%) scale(1.1);
        opacity: 0.8;
      }
    }
  `}
`;

const StyledCard = styled(Card)`
  ${({ theme }) => css`
    max-width: 440px;
    width: 100%;
    background: ${theme.colorBgContainer};
    border-radius: ${theme.borderRadiusLG}px;
    box-shadow: 0 8px 32px ${theme.colorPrimary}20,
                0 2px 8px ${theme.colorBorder};
    border: 1px solid ${theme.colorBorderSecondary};
    position: relative;
    z-index: 1;

    .ant-card-head {
      border-bottom: 1px solid ${theme.colorBorderSecondary};
      padding: ${theme.paddingLG}px ${theme.paddingXL}px;

      .ant-card-head-title {
        font-size: ${theme.fontSizeHeading3}px;
        font-weight: ${theme.fontWeightStrong};
        color: ${theme.colorText};
        text-align: center;
        padding: ${theme.paddingSM}px 0;
      }
    }

    .ant-card-body {
      padding: ${theme.paddingXL}px;
    }

    .ant-form-item-label label {
      color: ${theme.colorText};
      font-weight: ${theme.fontWeightStrong};
    }

    .ant-input-affix-wrapper,
    .ant-input-password {
      padding: ${theme.paddingSM}px ${theme.paddingMD}px;
      border-radius: ${theme.borderRadius}px;
      border: 1px solid ${theme.colorBorder};
      transition: all 0.3s ease;

      &:hover {
        border-color: ${theme.colorPrimaryHover};
      }

      &:focus,
      &:focus-within {
        border-color: ${theme.colorPrimary};
        box-shadow: 0 0 0 2px ${theme.colorPrimaryBg};
      }
    }

    .ant-btn-primary {
      height: 40px;
      font-weight: ${theme.fontWeightStrong};
      border-radius: ${theme.borderRadius}px;
      box-shadow: 0 2px 8px ${theme.colorPrimary}30;

      &:hover {
        box-shadow: 0 4px 12px ${theme.colorPrimary}40;
        transform: translateY(-1px);
      }

      &:active {
        transform: translateY(0);
      }
    }

    .ant-btn-default {
      height: 40px;
      border-radius: ${theme.borderRadius}px;
    }
  `}
`;

const StyledLabel = styled(Typography.Text)`
  ${({ theme }) => css`
    font-size: ${theme.fontSize}px;
    font-weight: ${theme.fontWeightStrong};
  `}
`;

const WelcomeText = styled(Typography.Text)`
  ${({ theme }) => css`
    font-size: ${theme.fontSize}px;
    color: ${theme.colorTextSecondary};
    text-align: center;
    display: block;
    margin-bottom: ${theme.marginMD}px;
  `}
`;

const BrandTitle = styled.div`
  ${({ theme }) => css`
    text-align: center;
    margin-bottom: ${theme.marginXL}px;

    h1 {
      font-size: ${theme.fontSizeHeading2}px;
      font-weight: ${theme.fontWeightStrong};
      color: ${theme.colorPrimary};
      margin: 0 0 ${theme.marginXS}px 0;
      background: linear-gradient(135deg, ${theme.colorPrimary} 0%, ${theme.colorPrimaryActive} 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    p {
      font-size: ${theme.fontSizeSM}px;
      color: ${theme.colorTextTertiary};
      margin: 0;
    }
  `}
`;

export default function Login() {
  const [form] = Form.useForm<LoginForm>();
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch();

  const bootstrapData = getBootstrapData();
  const nextUrl = useMemo(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      return params.get('next') || '';
    } catch (_error) {
      return '';
    }
  }, []);

  const loginEndpoint = useMemo(
    () => (nextUrl ? `/login/?next=${encodeURIComponent(nextUrl)}` : '/login/'),
    [nextUrl],
  );

  const buildProviderLoginUrl = (providerName: string) => {
    const base = `/login/${providerName}`;
    return nextUrl
      ? `${base}${base.includes('?') ? '&' : '?'}next=${encodeURIComponent(nextUrl)}`
      : base;
  };

  const authType: AuthType = bootstrapData.common.conf.AUTH_TYPE;
  const providers: Provider[] = bootstrapData.common.conf.AUTH_PROVIDERS;
  const authRegistration: boolean =
    bootstrapData.common.conf.AUTH_USER_REGISTRATION;

  // TODO: This is a temporary solution for showing login errors after form submission.
  // Should be replaced with proper SPA-style authentication (JSON API with error responses)
  // when Flask-AppBuilder is updated or we implement a custom login endpoint.
  useEffect(() => {
    const loginAttempted = sessionStorage.getItem('login_attempted');

    if (loginAttempted === 'true') {
      sessionStorage.removeItem('login_attempted');
      dispatch(addDangerToast(t('Invalid username or password')));
      // Clear password field for security
      form.setFieldsValue({ password: '' });
    }
  }, [dispatch, form]);

  const onFinish = (values: LoginForm) => {
    setLoading(true);

    // Mark that we're attempting login (for error detection after redirect)
    sessionStorage.setItem('login_attempted', 'true');

    // Use standard form submission for Flask-AppBuilder compatibility
    SupersetClient.postForm(loginEndpoint, values, '');
  };

  const getAuthIconElement = (
    providerName: string,
  ): React.JSX.Element | undefined => {
    if (!providerName || typeof providerName !== 'string') {
      return undefined;
    }
    const iconComponentName = `${capitalize(providerName)}Outlined`;
    const IconComponent = (Icons as Record<string, React.ComponentType<any>>)[
      iconComponentName
    ];

    if (IconComponent && typeof IconComponent === 'function') {
      return <IconComponent />;
    }
    return undefined;
  };

  return (
    <LoginContainer data-test="login-form">
      <StyledCard padded>
        <BrandTitle>
          <h1>Apache Superset</h1>
          <p>{t('Data Visualization Platform')}</p>
        </BrandTitle>

        {authType === AuthType.AuthOID && (
          <Flex justify="center" vertical gap="middle">
            <WelcomeText>
              {t('Choose your authentication provider')}
            </WelcomeText>
            <Form layout="vertical" requiredMark="optional" form={form}>
              {providers.map((provider: OIDProvider) => (
                <Form.Item<LoginForm> key={provider.name}>
                  <Button
                    href={buildProviderLoginUrl(provider.name)}
                    block
                    size="large"
                    iconPosition="start"
                    icon={getAuthIconElement(provider.name)}
                  >
                    {t('Sign in with')} {capitalize(provider.name)}
                  </Button>
                </Form.Item>
              ))}
            </Form>
          </Flex>
        )}

        {authType === AuthType.AuthOauth && (
          <Flex justify="center" gap={0} vertical>
            <WelcomeText>
              {t('Choose your authentication provider')}
            </WelcomeText>
            <Form layout="vertical" requiredMark="optional" form={form}>
              {providers.map((provider: OAuthProvider) => (
                <Form.Item<LoginForm> key={provider.name}>
                  <Button
                    href={buildProviderLoginUrl(provider.name)}
                    block
                    size="large"
                    iconPosition="start"
                    icon={getAuthIconElement(provider.name)}
                  >
                    {t('Sign in with')} {capitalize(provider.name)}
                  </Button>
                </Form.Item>
              ))}
            </Form>
          </Flex>
        )}

        {(authType === AuthType.AuthDB || authType === AuthType.AuthLDAP) && (
          <Flex justify="center" vertical gap="small">
            <WelcomeText>
              {t('Welcome back! Please sign in to continue')}
            </WelcomeText>
            <Form
              layout="vertical"
              requiredMark="optional"
              form={form}
              onFinish={onFinish}
            >
              <Form.Item<LoginForm>
                label={<StyledLabel>{t('Username')}</StyledLabel>}
                name="username"
                rules={[
                  { required: true, message: t('Please enter your username') },
                ]}
              >
                <Input
                  autoFocus
                  size="large"
                  placeholder={t('Enter your username')}
                  prefix={<Icons.UserOutlined iconSize="l" />}
                  data-test="username-input"
                />
              </Form.Item>
              <Form.Item<LoginForm>
                label={<StyledLabel>{t('Password')}</StyledLabel>}
                name="password"
                rules={[
                  { required: true, message: t('Please enter your password') },
                ]}
              >
                <Input.Password
                  size="large"
                  placeholder={t('Enter your password')}
                  prefix={<Icons.KeyOutlined iconSize="l" />}
                  data-test="password-input"
                />
              </Form.Item>
              <Form.Item label={null}>
                <Flex vertical gap="middle">
                  <Button
                    block
                    type="primary"
                    size="large"
                    htmlType="submit"
                    loading={loading}
                    data-test="login-button"
                  >
                    {t('Sign in')}
                  </Button>
                  {authRegistration && (
                    <Button
                      block
                      type="default"
                      size="large"
                      href="/register/"
                      data-test="register-button"
                    >
                      {t('Create an account')}
                    </Button>
                  )}
                </Flex>
              </Form.Item>
            </Form>
          </Flex>
        )}
      </StyledCard>
    </LoginContainer>
  );
}
