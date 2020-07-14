package vault

import (
	"errors"

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

				client, err := rVault.NewClient(rVault.DefaultConfig())
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

	secret, ok := secrets.Data[key].(string)
	if !ok {
		return "", nil
	}

	return secret, nil
}
