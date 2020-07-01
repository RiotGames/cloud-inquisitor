package settings

import (
	"fmt"
	"path/filepath"

	"github.com/spf13/viper"
)

func init() {
	viper.SetConfigName("settings")
	// lambda layer mount point
	viper.AddConfigPath("/opt")
	// if config is zipped with binary
	viper.AddConfigPath("./")
	if err := viper.ReadInConfig(); err != nil {
		fmt.Printf("recieved error reading config: %s\n", err.Error())
		paths := []string{"/opt/*", "./*"}
		for _, path := range paths {
			files, err2 := filepath.Glob(path)
			if err2 != nil {
				fmt.Printf("error reading files in dir %s: %s\n", path, err2.Error())
			} else {
				fmt.Printf("files in dir %s: %#v", path, files)
			}
		}
		panic(err)
	}
}

func Get(key string) interface{} {
	return viper.Get(key)
}

func GetString(key string) string {
	return viper.GetString(key)
}

func GetBool(key string) bool {
	return viper.GetBool(key)
}
