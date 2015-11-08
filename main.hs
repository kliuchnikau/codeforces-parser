#!/usr/bin/env runhaskell

{-import Control.Monad-}

doSmth2 :: Int -> Int
doSmth2 int = int + 2

main :: IO ()
main = do
  line <- getLine
  {-rows <- forM [1..8] (\a -> getLine)-}
  let int = read line :: Int

  putStrLn $ show $ int
