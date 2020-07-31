package vault

import (
	"errors"
	"fmt"
	"io/ioutil"
	"os"

	"github.com/RiotGames/cloud-inquisitor/cloud-inquisitor/settings"
	"go.riotgames.com/OpSec/rVault"
)

func newVaultClient() (*rVault.Client, error) {
	if settings.IsSet("vault") {
		if settings.IsSet("vault.auth_type") {
			switch settings.GetString("vault.auth_type") {
			case "iam":
				vaultRole := settings.GetString("vault.role")
				vaultAWSMount := settings.GetString("vault.auth_mount")
				// /vaultSecretMount := settings.GetString("vault.secret_mount")

				config := rVault.DefaultConfig()
				config.Address = settings.GetString("vault.address")

				client, err := rVault.NewClient(config)
				if err != nil {
					return nil, err
				}

				_, err = client.Auth.IAM.Login(rVault.IAMLoginOptions{
					Role:       vaultRole,
					MountPoint: vaultAWSMount})
				if err != nil {
					return nil, err
				}

				return client, nil
			case "token":
				config := rVault.DefaultConfig()
				client, err := rVault.NewClient(config)
				if err != nil {
					return nil, err
				}

				var token string
				if os.Getenv("VAULT_TOKEN") != "" {
					token = os.Getenv("VAULT_TOKEN")
				}

				var fileToken string
				if homeDir, homeErr := os.UserHomeDir(); homeErr == nil {
					if tokenVal, valErr := ioutil.ReadFile(homeDir + "/.vault-token"); valErr == nil {
						fileToken = string(tokenVal)
					} else {
						fmt.Println(valErr.Error())
					}
				} else {
					fmt.Println(homeErr.Error())
				}

				if fileToken != "" {
					token = fileToken
				}

				if token == "" {
					return nil, errors.New("unable to find token in env var VAULT_TOKEN or in file ~/.vault-token")
				}

				opts := rVault.TokenOptions{
					Token: token,
				}
				if _, loginErr := client.Auth.Token.Login(opts); loginErr != nil {
					return nil, loginErr
				}
				return client, nil
			default:
				return nil, errors.New("unsupported vault auth type")
			}
		} else {
			return nil, errors.New("no vault auth type set")
		}
	} else {
		return nil, errors.New("no vault config set")
	}
}

func GetString(path, key string) (string, error) {
	client, err := newVaultClient()
	if err != nil {
		return "", err
	}

	vaultSecretMount := settings.GetString("vault.secret_mount")
	secrets, err := client.KV2.Get(rVault.KV2GetOptions{
		MountPoint: vaultSecretMount,
		Path:       path,
	})

	if err != nil {
		return "", err
	}

	data, ok := secrets.Data["data"].(map[string]interface{})
	if !ok {
		return "", errors.New("vault data entry empty")
	} else {
		if secret, secretOk := data[key]; !secretOk {
			return "", errors.New("not a valid secret key")
		} else {
			if secretString, typeOk := secret.(string); !typeOk {
				return "", errors.New("retrieved value has invalid type")
			} else {
				return secretString, nil
			}
		}
	}

	return "", nil
}
