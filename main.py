import repository
import view



def main():
    config = repository.get_config()
    view.to_streamlit(config)

if __name__ == '__main__':
    main()
